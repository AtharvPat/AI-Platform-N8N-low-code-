# backend/graph/workflow.py - FIXED VERSION
from typing import Dict, Any, List
from collections import deque

from models.schemas import AgentState, ProcessingRequest, TaskType, ProcessingMode, LLMModel
from agents.csv_loader_agent import CSVLoaderAgent
from agents.preprocessor_agent import PreprocessorAgent
from agents.llm_agent import LLMAgent
from agents.output_agent import OutputAgent


class Workflow:
    """Workflow executor that can run a frontend-sent graph (nodes + edges + configs).

    The executor accepts a `ProcessingRequest` where `workflow` is an optional dict
    with `nodes` and `edges`. If no workflow is provided, it falls back to the
    original linear pipeline: load -> preprocess -> llm -> output.
    """

    def __init__(self):
        self.csv_loader = CSVLoaderAgent()
        self.preprocessor = PreprocessorAgent()
        self.llm_agent = LLMAgent()
        self.output_agent = OutputAgent()

    def _build_processing_request_from_node(self, base_request: ProcessingRequest, node_config: Dict[str, Any]) -> ProcessingRequest:
        """Create a ProcessingRequest instance from the base request and node config."""
        # Start from base request dict to preserve file_id and defaults
        base = base_request.dict()

        # Map possible node config keys into the request
        if node_config is None:
            return ProcessingRequest(**base)

        # Replace fields if provided
        if 'task' in node_config and node_config['task']:
            try:
                base['task'] = TaskType(node_config['task'])
            except Exception:
                base['task'] = base_request.task

        if 'mode' in node_config and node_config['mode']:
            try:
                base['mode'] = ProcessingMode(node_config['mode'])
            except Exception:
                base['mode'] = base_request.mode

        if 'llm_model' in node_config and node_config['llm_model']:
            try:
                base['llm_model'] = LLMModel(node_config['llm_model'])
            except Exception:
                base['llm_model'] = base_request.llm_model

        if 'batch_size' in node_config and node_config['batch_size']:
            base['batch_size'] = int(node_config['batch_size'])

        # Row range may be provided as start_row/end_row
        if 'start_row' in node_config or 'end_row' in node_config:
            start = int(node_config.get('start_row', 0))
            end = int(node_config.get('end_row', base.get('row_range', {}).get('end', 0) or 0))
            base['row_range'] = {'start': start, 'end': end}

        # product_ids if provided
        if 'product_ids' in node_config and node_config['product_ids']:
            base['product_ids'] = node_config['product_ids']

        return ProcessingRequest(**base)

    def _topological_sort(self, nodes: List[Dict[str, Any]], edges: List[Dict[str, str]]) -> List[str]:
        """Return a list of node ids in topological order. If cycle detected,
        returns nodes in insertion order as fallback."""
        node_ids = [n.get('id') or n.get('node_id') for n in nodes]
        adj: Dict[str, List[str]] = {nid: [] for nid in node_ids}
        indeg: Dict[str, int] = {nid: 0 for nid in node_ids}

        for e in edges or []:
            s = e.get('source')
            t = e.get('target')
            if s in adj:
                adj[s].append(t)
            if t in indeg:
                indeg[t] += 1

        q = deque([nid for nid, d in indeg.items() if d == 0])
        order: List[str] = []

        while q:
            u = q.popleft()
            order.append(u)
            for v in adj.get(u, []):
                indeg[v] -= 1
                if indeg[v] == 0:
                    q.append(v)

        # If not all nodes are in order, return insertion order as fallback
        if len(order) != len(node_ids):
            return node_ids

        return order

    def run_workflow_sync(self, file_path: str, config: ProcessingRequest) -> AgentState:
        """Run workflow synchronously. If `config.workflow` exists, execute the
        provided graph, otherwise run the default linear pipeline."""
        try:
            print(f"🚀 Starting workflow for file: {file_path}")

            # If no workflow provided, run original linear pipeline
            if not config.workflow:
                print("No workflow graph provided — running default pipeline")
                state = AgentState(file_path=file_path, task_config=config)
                state = self.csv_loader.load_file(state.file_path)
                if state.error:
                    return state
                state.task_config = config
                state = self.preprocessor.preprocess(state)
                if state.error:
                    return state
                state = self.llm_agent.process_batch_sync(state)
                if state.error:
                    return state
                state = self.output_agent.generate_output(state)
                return state

            # Execute graph-based workflow
            workflow = config.workflow
            nodes: List[Dict[str, Any]] = workflow.get('nodes', [])
            edges: List[Dict[str, str]] = workflow.get('edges', [])

            node_map = { (n.get('id') or n.get('node_id')): n for n in nodes }
            order = self._topological_sort(nodes, edges)

            print(f"Graph nodes order: {order}")

            # helper: get predecessors
            predecessors: Dict[str, List[str]] = {nid: [] for nid in node_map.keys()}
            for e in edges or []:
                s = e.get('source')
                t = e.get('target')
                if t in predecessors:
                    predecessors[t].append(s)

            # storage for each node's output state
            node_state_outputs: Dict[str, AgentState] = {}

            # base state (contains file info and original request)
            base_state = AgentState(file_path=file_path, task_config=config)

            for node_id in order:
                node = node_map.get(node_id)
                if node is None:
                    print(f"⚠️ Unknown node {node_id}, skipping")
                    continue

                node_type = node.get('type') or node.get('node_type')
                node_cfg = node.get('config') or {}

                # determine input state
                preds = predecessors.get(node_id, [])
                if preds:
                    # simple strategy: take first predecessor's state
                    input_state = node_state_outputs.get(preds[0], base_state)
                else:
                    input_state = base_state

                print(f"▶ Running node {node_id} (type={node_type})")

                try:
                    result_state = None

                    if node_type == 'upload':
                        # upload node reads the CSV from file_path
                        result_state = self.csv_loader.load_file(file_path)

                    elif node_type in ('filter', 'preprocess'):
                        # node_cfg may contain filtering params
                        # attach task config to state and run preprocessor
                        input_state.task_config = self._build_processing_request_from_node(config, node_cfg)
                        result_state = self.preprocessor.preprocess(input_state)

                    elif node_type in ('process', 'llm'):
                        # ensure preprocessed data exists
                        if not input_state.processed_data:
                            # run preprocessor first
                            tmp_req = self._build_processing_request_from_node(config, node_cfg)
                            input_state.task_config = tmp_req
                            input_state = self.preprocessor.preprocess(input_state)

                        # set task config from node
                        input_state.task_config = self._build_processing_request_from_node(config, node_cfg)
                        result_state = self.llm_agent.process_batch_sync(input_state)

                    elif node_type == 'output':
                        # generate output from the incoming state
                        result_state = self.output_agent.generate_output(input_state)

                    else:
                        # For database, api, email, webhook, etc. - pass through
                        print(f"ℹ️ Node type '{node_type}' not implemented as agent; passing state through")
                        result_state = input_state

                    if result_state is None:
                        result_state = AgentState(file_path=file_path, task_config=config, error=f"Node {node_id} produced no result")

                    # save node result
                    node_state_outputs[node_id] = result_state

                    if result_state.error:
                        print(f"❌ Node {node_id} failed: {result_state.error}")
                        return result_state

                except Exception as e:
                    err = f"Node {node_id} execution error: {str(e)}"
                    print(f"❌ {err}")
                    return AgentState(file_path=file_path, task_config=config, error=err)

            # After executing nodes, find terminal nodes (no outgoing edges)
            outgoing = {nid: 0 for nid in node_map.keys()}
            for e in edges or []:
                s = e.get('source')
                if s in outgoing:
                    outgoing[s] += 1

            terminal_nodes = [nid for nid, cnt in outgoing.items() if cnt == 0]
            final_state = None
            # pick a terminal node that produced results, otherwise first terminal
            for tn in terminal_nodes:
                st = node_state_outputs.get(tn)
                if st and (st.results or st.metadata.get('output_file')):
                    final_state = st
                    break

            if not final_state and terminal_nodes:
                final_state = node_state_outputs.get(terminal_nodes[0])

            if not final_state:
                # fallback: last executed node
                if order:
                    final_state = node_state_outputs.get(order[-1], AgentState(file_path=file_path, task_config=config))
                else:
                    final_state = AgentState(file_path=file_path, task_config=config, error="No nodes executed")

            print("✅ Graph workflow completed")
            return final_state

        except Exception as e:
            error_msg = f"Workflow error: {str(e)}"
            print(f"❌ {error_msg}")
            return AgentState(
                file_path=file_path,
                task_config=config,
                error=error_msg
            )