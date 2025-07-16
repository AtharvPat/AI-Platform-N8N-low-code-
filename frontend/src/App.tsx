// Replace frontend/src/App.tsx with this enhanced version with drag-and-drop sidebar:
import React, { useState, useCallback, useRef, DragEvent } from 'react';
import {
  ReactFlow,
  ReactFlowProvider,
  addEdge,
  useNodesState,
  useEdgesState,
  Controls,
  Background,
  Connection,
  MarkerType,
  Handle,
  Position,
  useReactFlow,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { 
  Upload, 
  Zap, 
  Download, 
  Settings, 
  Play, 
  FileText,
  Loader2,
  CheckCircle,
  AlertTriangle,
  X,
  Database,
  Filter,
  BarChart3,
  Mail,
  MessageSquare,
  Globe,
  Cpu,
  ArrowRight,
  Plus,
  Menu
} from 'lucide-react';

// Agent/Node Types Configuration
const AGENT_TYPES = {
  // Data Sources
  upload: { 
    label: 'File Upload', 
    icon: Upload, 
    color: 'bg-green-100 border-green-300 text-green-800',
    category: 'Input',
    description: 'Upload CSV, Excel, or JSON files'
  },
  database: { 
    label: 'Database', 
    icon: Database, 
    color: 'bg-blue-100 border-blue-300 text-blue-800',
    category: 'Input',
    description: 'Connect to SQL databases'
  },
  api: { 
    label: 'API Source', 
    icon: Globe, 
    color: 'bg-cyan-100 border-cyan-300 text-cyan-800',
    category: 'Input',
    description: 'Fetch data from REST APIs'
  },
  
  // Processing
  process: { 
    label: 'AI Processor', 
    icon: Zap, 
    color: 'bg-purple-100 border-purple-300 text-purple-800',
    category: 'Processing',
    description: 'Apply AI models to your data'
  },
  filter: { 
    label: 'Data Filter', 
    icon: Filter, 
    color: 'bg-orange-100 border-orange-300 text-orange-800',
    category: 'Processing',
    description: 'Filter and transform data'
  },
  llm: { 
    label: 'LLM Agent', 
    icon: Cpu, 
    color: 'bg-indigo-100 border-indigo-300 text-indigo-800',
    category: 'Processing',
    description: 'Advanced language model processing'
  },
  
  // Analysis
  analytics: { 
    label: 'Analytics', 
    icon: BarChart3, 
    color: 'bg-yellow-100 border-yellow-300 text-yellow-800',
    category: 'Analysis',
    description: 'Generate insights and reports'
  },
  
  // Output
  output: { 
    label: 'File Output', 
    icon: Download, 
    color: 'bg-gray-100 border-gray-300 text-gray-800',
    category: 'Output',
    description: 'Save results to files'
  },
  email: { 
    label: 'Email', 
    icon: Mail, 
    color: 'bg-red-100 border-red-300 text-red-800',
    category: 'Output',
    description: 'Send results via email'
  },
  webhook: { 
    label: 'Webhook', 
    icon: MessageSquare, 
    color: 'bg-teal-100 border-teal-300 text-teal-800',
    category: 'Output',
    description: 'Send data to external systems'
  },
};

// Sidebar Component
const Sidebar = () => {
  const onDragStart = (event: React.DragEvent<HTMLDivElement>, nodeType: string) => {
    console.log('Drag started for:', nodeType);
    event.dataTransfer.setData('application/reactflow', nodeType);
    event.dataTransfer.effectAllowed = 'move';
  };

  const categories = ['Input', 'Processing', 'Analysis', 'Output'];

  return (
    <div className="w-80 bg-white border-r border-gray-200 shadow-lg flex flex-col">
      <div className="p-4 border-b border-gray-200">
        <h2 className="text-lg font-semibold text-gray-900">AI Agents</h2>
        <p className="text-sm text-gray-600 mt-1">
          Drag agents onto the canvas to build your workflow
        </p>
      </div>

      <div className="p-4 space-y-6 overflow-y-auto flex-1">
        {categories.map((category) => (
          <div key={category}>
            <h3 className="text-sm font-medium text-gray-700 mb-3 flex items-center">
              <span className="h-2 w-2 bg-blue-500 rounded-full mr-2"></span>
              {category}
            </h3>
            <div className="space-y-2">
              {Object.entries(AGENT_TYPES)
                .filter(([_, config]) => config.category === category)
                .map(([type, config]) => {
                  const IconComponent = config.icon;
                  return (
                    <div
                      key={type}
                      draggable
                      onDragStart={(event) => onDragStart(event, type)}
                      className={`p-3 rounded-lg border-2 cursor-move hover:shadow-md transition-all ${config.color} hover:scale-105 select-none`}
                      style={{ userSelect: 'none' }}
                    >
                      <div className="flex items-center space-x-3">
                        <IconComponent className="h-5 w-5 flex-shrink-0" />
                        <div className="flex-1 min-w-0">
                          <div className="font-medium text-sm">{config.label}</div>
                          <div className="text-xs opacity-75 truncate">
                            {config.description}
                          </div>
                        </div>
                        <Plus className="h-4 w-4 opacity-50" />
                      </div>
                    </div>
                  );
                })}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// Enhanced Custom Node Component
const CustomNode = ({ data, id, selected }: any) => {
  const agentConfig = AGENT_TYPES[data.type as keyof typeof AGENT_TYPES];
  const IconComponent = agentConfig?.icon || FileText;

  const getStatusIcon = () => {
    switch (data.status) {
      case 'running': return <Loader2 className="h-3 w-3 animate-spin text-blue-600" />;
      case 'completed': return <CheckCircle className="h-3 w-3 text-green-600" />;
      case 'error': return <AlertTriangle className="h-3 w-3 text-red-600" />;
      default: return null;
    }
  };

  return (
    <div
      className={`px-4 py-3 shadow-lg rounded-lg border-2 min-w-[200px] transition-all cursor-pointer ${
        agentConfig?.color || 'bg-gray-100 border-gray-300 text-gray-800'
      } ${selected ? 'ring-2 ring-blue-500 ring-offset-2' : ''} ${
        !data.isConfigured && data.type !== 'upload' ? 'opacity-60' : ''
      }`}
    >
      {/* Input handle for non-input nodes */}
      {!['upload', 'database', 'api'].includes(data.type) && (
        <Handle
          type="target"
          position={Position.Left}
          className="w-3 h-3 bg-gray-400 border-2 border-white"
        />
      )}

      <div className="flex items-center space-x-3">
        <IconComponent className="h-5 w-5 flex-shrink-0" />
        <div className="flex-1 min-w-0">
          <div className="font-medium text-sm truncate">{data.label}</div>
          <div className="flex items-center space-x-2 mt-1">
            {data.config && Object.keys(data.config).length > 0 && (
              <div className="text-xs opacity-75">Configured</div>
            )}
            {getStatusIcon()}
          </div>
        </div>
        {data.type === 'process' && (
          <Settings className="h-4 w-4 opacity-50" />
        )}
      </div>

      {/* Output handle for non-output nodes */}
      {!['output', 'email', 'webhook'].includes(data.type) && (
        <Handle
          type="source"
          position={Position.Right}
          className="w-3 h-3 bg-gray-400 border-2 border-white"
        />
      )}
    </div>
  );
};

// Simple Node Types
const nodeTypes = {
  custom: CustomNode,
};

// Configuration Modal (keeping the existing one with minor updates)
interface ConfigModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (config: any) => void;
  nodeType: string;
  initialConfig?: any;
}

const ConfigModal: React.FC<ConfigModalProps> = ({
  isOpen,
  onClose,
  onSave,
  nodeType,
  initialConfig = {},
}) => {
  const [config, setConfig] = useState(initialConfig);

  if (!isOpen) return null;

  const handleSave = () => {
    onSave(config);
    onClose();
  };

  const renderConfigContent = () => {
    switch (nodeType) {
      case 'upload':
        return (
          <div>
            <h3 className="text-lg font-medium mb-4">File Upload Configuration</h3>
            <div className="space-y-4">
              <label className="flex flex-col items-center justify-center w-full h-32 border-2 border-gray-300 border-dashed rounded-lg cursor-pointer bg-gray-50 hover:bg-gray-100">
                <div className="flex flex-col items-center justify-center pt-5 pb-6">
                  <Upload className="w-8 h-8 mb-2 text-gray-500" />
                  <p className="mb-2 text-sm text-gray-500">
                    <span className="font-semibold">Click to upload</span> CSV file
                  </p>
                </div>
                <input
                  type="file"
                  className="hidden"
                  accept=".csv,.xlsx"
                  onChange={(e) => {
                    const file = e.target.files?.[0];
                    if (file) {
                      setConfig({ ...config, file, filename: file.name });
                    }
                  }}
                />
              </label>
              {config.filename && (
                <p className="text-sm text-green-600">Selected: {config.filename}</p>
              )}
            </div>
          </div>
        );

      case 'database':
        return (
          <div>
            <h3 className="text-lg font-medium mb-4">Database Configuration</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Database Type
                </label>
                <select
                  value={config.db_type || 'postgresql'}
                  onChange={(e) => setConfig({ ...config, db_type: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="postgresql">PostgreSQL</option>
                  <option value="mysql">MySQL</option>
                  <option value="sqlite">SQLite</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Connection String
                </label>
                <input
                  type="text"
                  value={config.connection_string || ''}
                  onChange={(e) => setConfig({ ...config, connection_string: e.target.value })}
                  placeholder="postgresql://user:password@localhost:5432/database"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
          </div>
        );

      case 'process':
      case 'llm':
        return (
          <div>
            <h3 className="text-lg font-medium mb-4">AI Processing Configuration</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  AI Task
                </label>
                <select
                  value={config.task || 'attribute_extraction'}
                  onChange={(e) => setConfig({ ...config, task: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="attribute_extraction">Attribute Extraction</option>
                  <option value="sales_faq">Sales FAQ Generation</option>
                  <option value="data_qa">Data Quality Analysis</option>
                  <option value="content_enrichment">Content Enrichment</option>
                  <option value="category_classification">Category Classification</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  LLM Model
                </label>
                <select
                  value={config.llm_model || 'gpt-3.5-turbo'}
                  onChange={(e) => setConfig({ ...config, llm_model: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                  <option value="gpt-4o-mini">GPT-4o Mini</option>
                  <option value="gpt-4o">GPT-4o</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Batch Size
                </label>
                <input
                  type="number"
                  min="1"
                  max="100"
                  value={config.batch_size || 5}
                  onChange={(e) => setConfig({ ...config, batch_size: parseInt(e.target.value) || 5 })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Start Row
                  </label>
                  <input
                    type="number"
                    min="0"
                    value={config.start_row || 0}
                    onChange={(e) => setConfig({ ...config, start_row: parseInt(e.target.value) || 0 })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    End Row
                  </label>
                  <input
                    type="number"
                    min="1"
                    value={config.end_row || 2}
                    onChange={(e) => setConfig({ ...config, end_row: parseInt(e.target.value) || 2 })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>
            </div>
          </div>
        );

      case 'output':
        return (
          <div>
            <h3 className="text-lg font-medium mb-4">Output Configuration</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Output Format
                </label>
                <select
                  value={config.format || 'csv'}
                  onChange={(e) => setConfig({ ...config, format: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="csv">CSV</option>
                  <option value="xlsx">Excel</option>
                  <option value="json">JSON</option>
                </select>
              </div>
            </div>
          </div>
        );

      default:
        return (
          <div>
            <h3 className="text-lg font-medium mb-4">
              {AGENT_TYPES[nodeType as keyof typeof AGENT_TYPES]?.label || 'Unknown'} Configuration
            </h3>
            <div className="space-y-4">
              <div className="text-sm text-gray-600">
                Configuration options for this agent type are coming soon.
              </div>
            </div>
          </div>
        );
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-6 border-b">
          <h2 className="text-xl font-semibold text-gray-900">
            Configure Agent
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        <div className="p-6">
          {renderConfigContent()}
        </div>

        <div className="flex justify-end space-x-3 p-6 border-t bg-gray-50">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-700 bg-gray-200 rounded-md hover:bg-gray-300 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            className="px-4 py-2 text-white bg-blue-600 rounded-md hover:bg-blue-700 transition-colors"
          >
            Save Configuration
          </button>
        </div>
      </div>
    </div>
  );
};

// Flow Component (inside ReactFlowProvider)
const FlowComponent = ({
  nodes,
  edges,
  onNodesChange,
  onEdgesChange,
  onConnect,
  onNodeClick,
  onDrop,
  onDragOver,
  nodeTypes,
}: any) => {
  return (
    <div 
      className="w-full h-full"
      onDrop={onDrop}
      onDragOver={onDragOver}
    >
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onNodeClick={onNodeClick}
        nodeTypes={nodeTypes}
        fitView
        attributionPosition="bottom-left"
      >
        <Background color="#f1f5f9" gap={20} />
        <Controls position="top-left" />
        
        {/* Drop Zone Hint */}
        <div className="absolute top-4 right-4 bg-white/90 backdrop-blur-sm border border-gray-200 rounded-lg p-4 shadow-sm max-w-xs pointer-events-none">
          <div className="flex items-center space-x-2 text-sm text-gray-600">
            <ArrowRight className="h-4 w-4" />
            <span>Drag agents from the sidebar to build your workflow</span>
          </div>
        </div>
      </ReactFlow>
    </div>
  );
};

// Main App Component
function App() {
  const [nodes, setNodes, onNodesChange] = useNodesState([
    {
      id: '1',
      type: 'custom',
      position: { x: 100, y: 100 },
      data: { label: 'File Upload', type: 'upload', isConfigured: false, status: 'idle' },
    },
    {
      id: '2',
      type: 'custom',
      position: { x: 400, y: 100 },
      data: { label: 'AI Processor', type: 'process', isConfigured: false, status: 'idle' },
    },
    {
      id: '3',
      type: 'custom',
      position: { x: 700, y: 100 },
      data: { label: 'Output', type: 'output', isConfigured: true, status: 'idle' },
    },
  ]);

  const [edges, setEdges, onEdgesChange] = useEdgesState([
    {
      id: 'e1-2',
      source: '1',
      target: '2',
      type: 'smoothstep',
      markerEnd: { type: MarkerType.ArrowClosed },
    },
    {
      id: 'e2-3',
      source: '2',
      target: '3',
      type: 'smoothstep',
      markerEnd: { type: MarkerType.ArrowClosed },
    },
  ]);

  const [configModal, setConfigModal] = useState({
    isOpen: false,
    nodeId: '',
    nodeType: '',
    initialConfig: {},
  });

  const [uploadedFile, setUploadedFile] = useState<any>(null);
  const [jobResult, setJobResult] = useState<any>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [nodeIdCounter, setNodeIdCounter] = useState(4);

  const reactFlowWrapper = useRef<HTMLDivElement>(null);

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  const onNodeClick = useCallback((event: React.MouseEvent, node: any) => {
    setConfigModal({
      isOpen: true,
      nodeId: node.id,
      nodeType: node.data.type,
      initialConfig: node.data.config || {},
    });
  }, []);

  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();
      console.log('Drop event triggered');

      const type = event.dataTransfer.getData('application/reactflow');
      console.log('Dropped type:', type);
      
      if (typeof type === 'undefined' || !type) {
        console.log('No type found in dataTransfer');
        return;
      }

      const reactFlowBounds = reactFlowWrapper.current?.getBoundingClientRect();
      if (!reactFlowBounds) {
        console.log('No reactFlowBounds found');
        return;
      }

      // Calculate position relative to the ReactFlow container
      const position = {
        x: event.clientX - reactFlowBounds.left - 100, // Offset to center the node
        y: event.clientY - reactFlowBounds.top - 50,
      };

      console.log('Calculated position:', position);

      const agentConfig = AGENT_TYPES[type as keyof typeof AGENT_TYPES];
      const newNode = {
        id: `${nodeIdCounter}`,
        type: 'custom',
        position,
        data: {
          label: agentConfig?.label || 'New Agent',
          type: type,
          isConfigured: false,
          status: 'idle',
        },
      };

      console.log('Creating new node:', newNode);
      setNodes((nds) => nds.concat(newNode));
      setNodeIdCounter((count) => count + 1);
    },
    [setNodes, nodeIdCounter]
  );

  const handleConfigSave = useCallback(
    (config: any) => {
      const { nodeId } = configModal;
      
      setNodes((nds: any) =>
        nds.map((node: any) =>
          node.id === nodeId
            ? {
                ...node,
                data: {
                  ...node.data,
                  config,
                  isConfigured: true,
                },
              }
            : node
        )
      );

      // Handle file upload
      if (configModal.nodeType === 'upload' && config.file) {
        handleFileUpload(config.file);
      }
    },
    [configModal, setNodes]
  );

  const handleFileUpload = async (file: File) => {
    updateNodeStatus('1', 'running');
    
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('http://localhost:8000/upload', {
        method: 'POST',
        body: formData,
      });
      
      if (response.ok) {
        const result = await response.json();
        setUploadedFile(result);
        updateNodeStatus('1', 'completed');
      } else {
        updateNodeStatus('1', 'error');
      }
    } catch (error) {
      console.error('Upload error:', error);
      updateNodeStatus('1', 'error');
    }
  };

  const updateNodeStatus = (nodeId: string, status: 'idle' | 'running' | 'completed' | 'error') => {
    setNodes((nds: any) =>
      nds.map((node: any) =>
        node.id === nodeId
          ? { ...node, data: { ...node.data, status } }
          : node
      )
    );
  };

  const runWorkflow = async () => {
    if (!uploadedFile) {
      alert('Please upload a file first');
      return;
    }

    const processNode = nodes.find((n: any) => n.data.type === 'process');
    const nodeData = processNode?.data as any;
    
    if (!nodeData?.config) {
      alert('Please configure the AI processor');
      return;
    }

    const config = nodeData.config;
    setIsRunning(true);
    updateNodeStatus('2', 'running');

    const requestData = {
      file_id: uploadedFile.file_id,
      task: config.task || 'attribute_extraction',
      mode: 'batch',
      llm_model: config.llm_model || 'gpt-3.5-turbo',
      batch_size: config.batch_size || 5,
      row_range: {
        start: config.start_row || 0,
        end: config.end_row || 2,
      },
    };

    try {
      const response = await fetch('http://localhost:8000/process', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestData),
      });

      if (response.ok) {
        const result = await response.json();
        setJobResult(result);
        pollJobStatus(result.job_id);
      } else {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
        alert(`Processing failed: ${errorData.detail || 'Unknown error'}`);
        updateNodeStatus('2', 'error');
        setIsRunning(false);
      }
    } catch (error) {
      console.error('Network error:', error);
      alert(`Network error: ${error}`);
      updateNodeStatus('2', 'error');
      setIsRunning(false);
    }
  };

  const pollJobStatus = async (jobId: string) => {
    const interval = setInterval(async () => {
      try {
        const response = await fetch(`http://localhost:8000/jobs/${jobId}`);
        if (response.ok) {
          const status = await response.json();
          setJobResult(status);
          
          if (status.status === 'completed') {
            updateNodeStatus('2', 'completed');
            updateNodeStatus('3', 'completed');
            setIsRunning(false);
            clearInterval(interval);
          } else if (status.status === 'failed') {
            updateNodeStatus('2', 'error');
            setIsRunning(false);
            clearInterval(interval);
          }
        }
      } catch (error) {
        console.error('Polling error:', error);
      }
    }, 2000);

    setTimeout(() => {
      clearInterval(interval);
      setIsRunning(false);
    }, 300000);
  };

  const downloadResults = async () => {
    if (!jobResult?.job_id) return;

    try {
      const response = await fetch(`http://localhost:8000/download/${jobResult.job_id}`);
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `results_${jobResult.job_id}.csv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
      }
    } catch (error) {
      console.error('Download error:', error);
    }
  };

  return (
    <ReactFlowProvider>
      <div className="h-screen flex bg-gray-50">
        {/* Sidebar - Always Visible */}
        <Sidebar />

        {/* Main Content Area */}
        <div className="flex-1 flex flex-col">
          {/* Header */}
          <header className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">AI Platform</h1>
              <p className="text-sm text-gray-600">Visual AI Workflow Builder</p>
            </div>
            
            <div className="flex items-center space-x-4">
              {uploadedFile && (
                <div className="flex items-center space-x-2 text-sm text-gray-600">
                  <FileText className="h-4 w-4" />
                  <span>{uploadedFile.filename} ({uploadedFile.row_count} rows)</span>
                </div>
              )}

              {jobResult && (
                <div className="flex items-center space-x-2 text-sm">
                  {jobResult.status === 'processing' && <Loader2 className="h-4 w-4 animate-spin text-blue-600" />}
                  {jobResult.status === 'completed' && <CheckCircle className="h-4 w-4 text-green-600" />}
                  {jobResult.status === 'failed' && <AlertTriangle className="h-4 w-4 text-red-600" />}
                  <span className="capitalize">{jobResult.status}</span>
                </div>
              )}

              <div className="flex items-center space-x-2">
                <button
                  onClick={runWorkflow}
                  disabled={isRunning || !uploadedFile}
                  className="flex items-center space-x-2 bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Play className="h-4 w-4" />
                  <span>{isRunning ? 'Running...' : 'Run Workflow'}</span>
                </button>

                {jobResult?.status === 'completed' && (
                  <button
                    onClick={downloadResults}
                    className="flex items-center space-x-2 bg-purple-600 text-white px-4 py-2 rounded-md hover:bg-purple-700 transition-colors"
                  >
                    <Download className="h-4 w-4" />
                    <span>Download</span>
                  </button>
                )}
              </div>
            </div>
          </header>

          {/* Workflow Canvas */}
          <div className="flex-1" ref={reactFlowWrapper}>
            <FlowComponent
              nodes={nodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onConnect={onConnect}
              onNodeClick={onNodeClick}
              onDrop={onDrop}
              onDragOver={onDragOver}
              nodeTypes={nodeTypes}
            />
          </div>
        </div>

        {/* Configuration Modal */}
        <ConfigModal
          isOpen={configModal.isOpen}
          onClose={() => setConfigModal({ ...configModal, isOpen: false })}
          onSave={handleConfigSave}
          nodeType={configModal.nodeType}
          initialConfig={configModal.initialConfig}
        />
      </div>
    </ReactFlowProvider>
  );
}

export default App;