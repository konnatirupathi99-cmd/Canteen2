import React from 'react';
import { Database, Activity, PackageCheck, Truck, ArrowRight, BrainCircuit } from 'lucide-react';
import './DigitalTwin.css';

export default function DigitalTwin() {
  return (
    <div className="digital-twin-page">
      <div className="twin-header card">
        <div className="twin-title-area">
          <BrainCircuit size={32} className="text-primary" />
          <div>
            <h3>Operational Digital Twin</h3>
            <p>Real-time simulation & optimization engine</p>
          </div>
        </div>
        <div className="twin-status">
          <div className="status-badge"><span className="live-indicator"></span> SIMULATION ACTIVE</div>
          <div className="sync-info">Last synced: Just now</div>
        </div>
      </div>

      <div className="twin-visualizer">
        
        {/* Node 1: Demand & Orders */}
        <div className="twin-node card">
          <div className="node-header">
            <Activity className="text-info" />
            <h4>Demand & Orders</h4>
          </div>
          <div className="node-metrics">
            <div className="metric">
              <span className="label">Live Volume</span>
              <span className="value">128 / hr</span>
            </div>
            <div className="metric">
              <span className="label">Predicted (Next Hr)</span>
              <span className="value text-warning">185 / hr</span>
            </div>
          </div>
        </div>

        <ArrowRight className="connector text-secondary" size={32} />

        {/* Node 2: Kitchen KDS */}
        <div className="twin-node card">
          <div className="node-header">
            <Database className="text-warning" />
            <h4>Kitchen Capacity</h4>
          </div>
          <div className="node-metrics">
            <div className="metric">
              <span className="label">Current Load</span>
              <span className="value">85%</span>
            </div>
            <div className="metric">
              <span className="label">Simulated Load</span>
              <span className="value text-danger">112% (Bottleneck)</span>
            </div>
          </div>
        </div>

        <ArrowRight className="connector text-secondary" size={32} />

        {/* Node 3: Inventory */}
        <div className="twin-node card">
          <div className="node-header">
            <PackageCheck className="text-success" />
            <h4>Inventory State</h4>
          </div>
          <div className="node-metrics">
            <div className="metric">
              <span className="label">Stock Level</span>
              <span className="value">Healthy</span>
            </div>
            <div className="metric">
              <span className="label">Depletion Risk</span>
              <span className="value text-warning">High (Veg Meals)</span>
            </div>
          </div>
        </div>

      </div>

      <div className="optimization-center grid-cols-2">
        <div className="card strategy-card">
          <h4>Current Operational Strategy</h4>
          <div className="strategy-detail">
            <strong>Standard Fulfillment</strong>
            <p>Orders processed sequentially based on arrival time. Default kitchen routing.</p>
          </div>
          <div className="impact-metrics">
            <div className="impact-item">Avg Wait: 8m 12s</div>
            <div className="impact-item">Fulfillment: 98%</div>
          </div>
        </div>

        <div className="card strategy-card recommended">
          <div className="recommended-badge">AI RECOMMENDED</div>
          <h4>Peak Hour Optimization</h4>
          <div className="strategy-detail">
            <strong>Dynamic Batching & Load Shedding</strong>
            <p>Automatically batch similar items (e.g. Veg Meals) and route to specialized prep stations.</p>
          </div>
          <div className="impact-metrics">
            <div className="impact-item text-success">↓ Expected Wait: 5m 30s</div>
            <div className="impact-item text-success">↓ Bottleneck Risk: Eliminated</div>
          </div>
          <button className="btn btn-primary mt-4 w-full">APPLY OPTIMIZATION</button>
        </div>
      </div>
    </div>
  );
}
