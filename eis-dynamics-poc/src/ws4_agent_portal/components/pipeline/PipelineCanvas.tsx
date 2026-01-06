"use client";

import { useCallback, useMemo } from "react";
import {
  ReactFlow,
  Node,
  Edge,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  BackgroundVariant,
  MarkerType,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import { AgentNode, AgentNodeData, AgentStatus } from "./AgentNode";
import { PipelineRun } from "@/lib/pipeline-api";

interface PipelineCanvasProps {
  pipelineRun?: PipelineRun | null;
  onNodeClick?: (agentType: string) => void;
}

// Custom node types
const nodeTypes = {
  agent: AgentNode,
};

// Initial node positions
const initialNodes: Node<AgentNodeData>[] = [
  {
    id: "router",
    type: "agent",
    position: { x: 50, y: 150 },
    data: {
      label: "Router Agent",
      agentType: "router",
      status: "pending",
    },
  },
  {
    id: "bronze",
    type: "agent",
    position: { x: 300, y: 50 },
    data: {
      label: "Bronze Agent",
      agentType: "bronze",
      status: "pending",
    },
  },
  {
    id: "silver",
    type: "agent",
    position: { x: 550, y: 150 },
    data: {
      label: "Silver Agent",
      agentType: "silver",
      status: "pending",
    },
  },
  {
    id: "gold",
    type: "agent",
    position: { x: 800, y: 150 },
    data: {
      label: "Gold Agent",
      agentType: "gold",
      status: "pending",
    },
  },
];

// Initial edges
const initialEdges: Edge[] = [
  {
    id: "router-bronze",
    source: "router",
    target: "bronze",
    animated: false,
    style: { stroke: "#94a3b8", strokeWidth: 2 },
    markerEnd: { type: MarkerType.ArrowClosed, color: "#94a3b8" },
  },
  {
    id: "bronze-silver",
    source: "bronze",
    target: "silver",
    animated: false,
    style: { stroke: "#94a3b8", strokeWidth: 2 },
    markerEnd: { type: MarkerType.ArrowClosed, color: "#94a3b8" },
  },
  {
    id: "silver-gold",
    source: "silver",
    target: "gold",
    animated: false,
    style: { stroke: "#94a3b8", strokeWidth: 2 },
    markerEnd: { type: MarkerType.ArrowClosed, color: "#94a3b8" },
  },
];

function getAgentStatus(state: { status: string } | null): AgentStatus {
  if (!state) return "pending";
  switch (state.status) {
    case "completed":
      return "completed";
    case "running":
      return "running";
    case "failed":
      return "failed";
    default:
      return "pending";
  }
}

export function PipelineCanvas({ pipelineRun, onNodeClick }: PipelineCanvasProps) {
  // Calculate nodes based on pipeline run state
  const nodes = useMemo<Node<AgentNodeData>[]>(() => {
    if (!pipelineRun) return initialNodes;

    return [
      {
        ...initialNodes[0],
        data: {
          ...initialNodes[0].data,
          status: getAgentStatus(pipelineRun.router_state),
          complexity: pipelineRun.complexity,
          processingTime: pipelineRun.router_state?.processing_time_ms,
        },
      },
      {
        ...initialNodes[1],
        data: {
          ...initialNodes[1].data,
          status: getAgentStatus(pipelineRun.bronze_state),
          decision: (pipelineRun.bronze_state?.output as Record<string, unknown>)?.decision as string,
          qualityScore: (pipelineRun.bronze_state?.output as Record<string, unknown>)?.quality_score as number,
          processingTime: pipelineRun.bronze_state?.processing_time_ms,
        },
      },
      {
        ...initialNodes[2],
        data: {
          ...initialNodes[2].data,
          status: getAgentStatus(pipelineRun.silver_state),
          processingTime: pipelineRun.silver_state?.processing_time_ms,
        },
      },
      {
        ...initialNodes[3],
        data: {
          ...initialNodes[3].data,
          status: getAgentStatus(pipelineRun.gold_state),
          decision: (pipelineRun.gold_state?.output as Record<string, unknown>)?.final_decision as string,
          riskLevel: (pipelineRun.gold_state?.output as Record<string, unknown>)?.risk_level as string,
          processingTime: pipelineRun.gold_state?.processing_time_ms,
        },
      },
    ];
  }, [pipelineRun]);

  // Calculate edges based on current stage
  const edges = useMemo<Edge[]>(() => {
    if (!pipelineRun) return initialEdges;

    const currentStage = pipelineRun.current_stage;
    const stageOrder = ["router", "bronze", "silver", "gold"];
    const currentIndex = stageOrder.indexOf(currentStage);

    return initialEdges.map((edge, index) => {
      const isActive = index < currentIndex || pipelineRun.status === "completed";
      const isAnimated = index === currentIndex - 1 && pipelineRun.status === "running";

      return {
        ...edge,
        animated: isAnimated,
        style: {
          ...edge.style,
          stroke: isActive ? "#22c55e" : "#94a3b8",
        },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: isActive ? "#22c55e" : "#94a3b8",
        },
      };
    });
  }, [pipelineRun]);

  const [nodesState, setNodes, onNodesChange] = useNodesState(nodes);
  const [edgesState, setEdges, onEdgesChange] = useEdgesState(edges);

  // Update nodes when pipeline run changes
  useMemo(() => {
    setNodes(nodes);
    setEdges(edges);
  }, [nodes, edges, setNodes, setEdges]);

  const handleNodeClick = useCallback(
    (_: React.MouseEvent, node: Node) => {
      if (onNodeClick) {
        onNodeClick(node.id);
      }
    },
    [onNodeClick]
  );

  return (
    <div className="h-[400px] w-full bg-gray-50 rounded-xl border border-gray-200 overflow-hidden">
      <ReactFlow
        nodes={nodesState}
        edges={edgesState}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={handleNodeClick}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        minZoom={0.5}
        maxZoom={1.5}
        proOptions={{ hideAttribution: true }}
      >
        <Background variant={BackgroundVariant.Dots} gap={16} size={1} />
        <Controls position="bottom-right" />
        <MiniMap
          position="bottom-left"
          nodeColor={(node) => {
            const data = node.data as AgentNodeData;
            switch (data.agentType) {
              case "router":
                return "#3b82f6";
              case "bronze":
                return "#f97316";
              case "silver":
                return "#6b7280";
              case "gold":
                return "#eab308";
              default:
                return "#94a3b8";
            }
          }}
          maskColor="rgba(0,0,0,0.1)"
        />
      </ReactFlow>
    </div>
  );
}
