from flask import Blueprint, jsonify, request
from app.models.order import Order, OrderItem, Fulfillment
from app.models.inventory import Inventory, InventoryTransaction
from app.models.product import Product
from app.extensions import db
from app.auth.middleware import require_auth, require_role
from datetime import datetime, timedelta
from sqlalchemy import func

analytics_bp = Blueprint('analytics', __name__, url_prefix='/api/v1/analytics')

@analytics_bp.route('/overview', methods=['GET'])
@require_auth
@require_role(['ORG_ADMIN', 'CANTEEN_MANAGER'])
def get_overview(current_user):
    """
    Returns today's high-level KPIs.
    """
    # For MVP, we define "today" as from midnight UTC to now.
    # In a real app, this should respect the canteen timezone.
    now = datetime.utcnow()
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # 1. Today's Revenue & Orders
    orders_today_query = db.session.query(
        func.count(Order.id).label('total_orders'),
        func.sum(Order.total).label('total_revenue')
    ).filter(
        Order.created_at >= start_of_day,
        Order.status != 'CANCELLED' # Include completed and active orders for revenue
    ).first()

    total_orders = orders_today_query.total_orders or 0
    total_revenue = float(orders_today_query.total_revenue or 0)
    
    # 2. Items Sold Today
    items_sold_query = db.session.query(
        func.sum(OrderItem.quantity)
    ).join(Order).filter(
        Order.created_at >= start_of_day,
        Order.status != 'CANCELLED'
    ).scalar()
    items_sold = int(items_sold_query or 0)

    # 3. Active Orders (Not Cancelled or Fulfilled)
    active_orders = db.session.query(func.count(Order.id)).filter(
        Order.status.in_(['PLACED', 'PREPARING', 'READY'])
    ).scalar()

    # 4. Inventory Metrics
    inventory_stats = db.session.query(
        func.sum(db.case((Inventory.quantity == 0, 1), else_=0)).label('out_of_stock'),
        func.sum(db.case(((Inventory.quantity > 0) & (Inventory.quantity <= Inventory.low_stock_threshold), 1), else_=0)).label('low_stock')
    ).first()
    
    out_of_stock = int(inventory_stats.out_of_stock or 0)
    low_stock = int(inventory_stats.low_stock or 0)

    average_order_value = (total_revenue / total_orders) if total_orders > 0 else 0.0

    return jsonify(success=True, data={
        "orders": total_orders,
        "revenue": total_revenue,
        "items_sold": items_sold,
        "active_orders": active_orders,
        "out_of_stock": out_of_stock,
        "low_stock": low_stock,
        "average_order_value": round(average_order_value, 2)
    })

def get_date_range(request):
    try:
        start = request.args.get('start_date')
        end = request.args.get('end_date')
        if start:
            start_date = datetime.fromisoformat(start.replace('Z', '+00:00')).replace(tzinfo=None)
        else:
            start_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            
        if end:
            end_date = datetime.fromisoformat(end.replace('Z', '+00:00')).replace(tzinfo=None)
        else:
            end_date = datetime.utcnow()
        return start_date, end_date
    except Exception:
        return datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0), datetime.utcnow()

@analytics_bp.route('/sales', methods=['GET'])
@require_auth
@require_role(['ORG_ADMIN', 'CANTEEN_MANAGER'])
def get_sales(current_user):
    """
    Sales trend and peak hours.
    """
    start_date, end_date = get_date_range(request)

    # 1. Hourly Revenue/Orders
    # In SQLite, extracting hour is slightly manual via strftime
    # But we can just fetch all orders in range and group in memory for MVP, assuming data fits.
    # For large datasets, use SQL GROUP BY.
    orders = Order.query.filter(
        Order.created_at >= start_date,
        Order.created_at <= end_date,
        Order.status != 'CANCELLED'
    ).all()
    
    hourly_data = {}
    for o in orders:
        hr = o.created_at.strftime('%Y-%m-%d %H:00')
        if hr not in hourly_data:
            hourly_data[hr] = {"orders": 0, "revenue": 0}
        hourly_data[hr]["orders"] += 1
        hourly_data[hr]["revenue"] += float(o.total)
        
    trend = [{"time": k, "orders": v["orders"], "revenue": v["revenue"]} for k, v in hourly_data.items()]
    trend.sort(key=lambda x: x["time"])
    
    # Peak hour
    peak_hour = max(trend, key=lambda x: x["orders"]) if trend else None

    return jsonify(success=True, data={
        "trend": trend,
        "peak_hour": peak_hour
    })

@analytics_bp.route('/products', methods=['GET'])
@require_auth
@require_role(['ORG_ADMIN', 'CANTEEN_MANAGER'])
def get_products_analytics(current_user):
    """
    Top selling products.
    """
    start_date, end_date = get_date_range(request)
    
    # Get top products by quantity sold
    top_products_query = db.session.query(
        OrderItem.product_name_snapshot,
        func.sum(OrderItem.quantity).label('units_sold'),
        func.sum(OrderItem.subtotal).label('revenue')
    ).join(Order).filter(
        Order.created_at >= start_date,
        Order.created_at <= end_date,
        Order.status != 'CANCELLED'
    ).group_by(OrderItem.product_name_snapshot).order_by(db.text('units_sold DESC')).limit(10).all()
    
    top_products = [{
        "name": row.product_name_snapshot,
        "units_sold": int(row.units_sold),
        "revenue": float(row.revenue)
    } for row in top_products_query]
    
    return jsonify(success=True, data={
        "top_products": top_products
    })

@analytics_bp.route('/stalls', methods=['GET'])
@require_auth
@require_role(['ORG_ADMIN', 'CANTEEN_MANAGER'])
def get_stalls_analytics(current_user):
    """
    Stall performance.
    """
    start_date, end_date = get_date_range(request)
    
    stall_performance_query = db.session.query(
        Fulfillment.stall_id,
        func.count(Fulfillment.id).label('orders'),
        # To calculate revenue per stall, we need order items
    ).join(Order).filter(
        Order.created_at >= start_date,
        Order.created_at <= end_date,
        Order.status != 'CANCELLED'
    ).group_by(Fulfillment.stall_id).all()
    
    # Actually, let's join Stall for name
    from app.models.stall import Stall
    
    stalls = Stall.query.all()
    stall_map = {s.id: s.name for s in stalls}
    
    results = []
    for row in stall_performance_query:
        # Get revenue
        rev_query = db.session.query(func.sum(OrderItem.subtotal)).filter(
            OrderItem.fulfillment_id == row.stall_id,
            OrderItem.order_id.in_(
                db.session.query(Order.id).filter(Order.created_at >= start_date, Order.created_at <= end_date, Order.status != 'CANCELLED')
            )
        ).scalar()
        
        results.append({
            "stall_id": row.stall_id,
            "stall_name": stall_map.get(row.stall_id, "Unknown"),
            "orders": int(row.orders),
            "revenue": float(rev_query or 0)
        })
        
    results.sort(key=lambda x: x["revenue"], reverse=True)
        
    return jsonify(success=True, data=results)

@analytics_bp.route('/fulfillment', methods=['GET'])
@require_auth
@require_role(['ORG_ADMIN', 'CANTEEN_MANAGER'])
def get_fulfillment_analytics(current_user):
    """
    Kitchen Performance / Fulfillment Analytics.
    """
    start_date, end_date = get_date_range(request)
    
    # We would calculate average fulfillment time.
    # Currently, Fulfillment model has created_at and updated_at.
    # If status is FULFILLED, (updated_at - created_at) is the total fulfillment time.
    completed_fulfillments = Fulfillment.query.filter(
        Fulfillment.created_at >= start_date,
        Fulfillment.created_at <= end_date,
        Fulfillment.status == 'FULFILLED'
    ).all()
    
    total_seconds = 0
    count = len(completed_fulfillments)
    for f in completed_fulfillments:
        delta = f.updated_at - f.created_at
        total_seconds += delta.total_seconds()
        
    avg_seconds = total_seconds / count if count > 0 else 0
    
    delayed_orders = db.session.query(func.count(Order.id)).filter(
        Order.status.in_(['PLACED', 'PREPARING']),
        Order.created_at < (datetime.utcnow() - timedelta(minutes=15)) # 15 min threshold
    ).scalar()
    
    return jsonify(success=True, data={
        "average_fulfillment_seconds": avg_seconds,
        "completed_count": count,
        "delayed_orders_count": delayed_orders
    })

@analytics_bp.route('/inventory', methods=['GET'])
@require_auth
@require_role(['ORG_ADMIN', 'CANTEEN_MANAGER'])
def get_inventory_analytics(current_user):
    """
    Inventory risk, waste, demand velocity, restock recommendations.
    """
    start_date, end_date = get_date_range(request)
    
    # 1. Waste Analytics
    waste_query = db.session.query(
        func.sum(InventoryTransaction.quantity_change).label('waste_qty')
    ).filter(
        InventoryTransaction.created_at >= start_date,
        InventoryTransaction.created_at <= end_date,
        InventoryTransaction.transaction_type == 'MANUAL_ADJUSTMENT',
        InventoryTransaction.quantity_change < 0
    ).scalar()
    
    total_waste = abs(int(waste_query or 0))

    # 2. Demand Velocity & Restock Recommendations
    # For MVP: demand velocity = units sold over the date range / hours in range
    # Or simply: total units sold in the date range
    sales_velocity_query = db.session.query(
        OrderItem.product_id,
        func.sum(OrderItem.quantity).label('units_sold')
    ).join(Order).filter(
        Order.created_at >= start_date,
        Order.created_at <= end_date,
        Order.status != 'CANCELLED'
    ).group_by(OrderItem.product_id).all()
    
    velocity_map = {row.product_id: int(row.units_sold) for row in sales_velocity_query}
    
    # Analyze all products to find risk
    products = Product.query.all()
    recommendations = []
    risks = []
    
    for p in products:
        inv = p.inventory
        if not inv: continue
        
        velocity = velocity_map.get(p.id, 0)
        # simplistic hourly velocity: assuming range is 24 hours
        hourly_velocity = velocity / 24.0 if velocity > 0 else 0.0
        
        # Risk estimation
        if hourly_velocity > 0 and inv.quantity > 0:
            hours_left = inv.quantity / hourly_velocity
            if hours_left <= 2:
                risks.append({
                    "product_id": p.id,
                    "product_name": p.name,
                    "current_stock": inv.quantity,
                    "velocity_per_hour": round(hourly_velocity, 2),
                    "estimated_exhaustion_hours": round(hours_left, 1),
                    "message": f"{p.name} may run out in ~{round(hours_left, 1)} hours"
                })
        
        # Restock Recommendation
        # expected demand (next 24h) = velocity
        # safety stock = threshold
        expected_demand = velocity
        safety_stock = inv.low_stock_threshold
        
        if inv.quantity <= safety_stock:
            recommended = max(0, expected_demand + safety_stock - inv.quantity)
            if recommended > 0:
                recommendations.append({
                    "product_id": p.id,
                    "product_name": p.name,
                    "current_stock": inv.quantity,
                    "expected_demand": expected_demand,
                    "safety_stock": safety_stock,
                    "recommended_quantity": recommended
                })
                
    return jsonify(success=True, data={
        "total_waste": total_waste,
        "stockout_risks": risks,
        "restock_recommendations": recommendations
    })

@analytics_bp.route('/alerts', methods=['GET'])
@require_auth
@require_role(['ORG_ADMIN', 'CANTEEN_MANAGER'])
def get_alerts(current_user):
    """
    Get all active alerts.
    """
    from app.models.alert import Alert
    
    alerts = Alert.query.filter_by(status='ACTIVE').all()
    
    # Simple severity sort trick: CRITICAL, WARNING, INFO (which alphabetically is C, W, I, so desc() kind of works if it's enum-based, but we'll sort manually).
    severity_order = {'CRITICAL': 3, 'WARNING': 2, 'INFO': 1}
    alerts.sort(key=lambda a: (severity_order.get(a.severity, 0), a.created_at), reverse=True)
    
    return jsonify(success=True, data=[{
        "id": a.id,
        "type": a.alert_type,
        "severity": a.severity,
        "message": a.message,
        "product_id": a.product_id,
        "stall_id": a.stall_id,
        "status": a.status,
        "created_at": a.created_at.isoformat(),
        "last_triggered_at": a.last_triggered_at.isoformat() if a.last_triggered_at else None
    } for a in alerts])

@analytics_bp.route('/alerts/<int:alert_id>/acknowledge', methods=['PUT'])
@require_auth
@require_role(['ORG_ADMIN', 'CANTEEN_MANAGER'])
def acknowledge_alert(current_user, alert_id):
    """
    Acknowledge an alert.
    """
    from app.models.alert import Alert
    
    alert = Alert.query.get(alert_id)
    if not alert:
        return jsonify(success=False, error={"code": "NOT_FOUND", "message": "Alert not found"}), 404
        
    if alert.status != 'ACTIVE':
        return jsonify(success=False, error={"code": "BAD_STATE", "message": "Alert is not active"}), 400
        
    alert.status = 'ACKNOWLEDGED'
    db.session.commit()
    
    return jsonify(success=True, data={"id": alert.id, "status": alert.status})
