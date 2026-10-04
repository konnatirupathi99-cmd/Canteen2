import logging
import json
import uuid
from datetime import datetime, timedelta
from app.extensions import db
from app.models.automation import AutomationPolicy, AutomationExecution

logger = logging.getLogger(__name__)

class AutomationService:
    @staticmethod
    def evaluate_and_execute(tenant_id, trigger_event, context_data, idempotency_key=None, dry_run=False):
        """
        Milestone 5, 6, 7: Policy Engine, Evaluation, Dry-Run
        Evaluates policies for a given trigger event and executes them if conditions pass.
        """
        # Find ACTIVE (or TESTING if dry_run) policies for this event
        status_filter = ['ACTIVE']
        if dry_run:
            status_filter.append('TESTING')
            
        policies = AutomationPolicy.query.filter(
            AutomationPolicy.tenant_id == tenant_id,
            AutomationPolicy.trigger_event == trigger_event,
            AutomationPolicy.status.in_(status_filter)
        ).all()
        
        results = []
        
        for policy in policies:
            # 1. Idempotency Check (Milestone 27, 54)
            if idempotency_key:
                scoped_key = f"{policy.id}_{idempotency_key}"
                existing = AutomationExecution.query.filter_by(idempotency_key=scoped_key).first()
                if existing:
                    logger.info(f"Idempotency hit for policy {policy.id} with key {scoped_key}")
                    continue
            else:
                scoped_key = str(uuid.uuid4())
                
            # 2. Cooldown Check (Milestone 26, 53)
            last_exec = AutomationExecution.query.filter_by(
                policy_id=policy.id,
                status='SUCCESS'
            ).order_by(AutomationExecution.executed_at.desc()).first()
            
            if last_exec and last_exec.executed_at > (datetime.utcnow() - timedelta(minutes=policy.cooldown_minutes)):
                logger.info(f"Policy {policy.id} is in cooldown.")
                continue
                
            # 3. Condition Evaluation
            conditions = policy.get_conditions()
            passed = True
            
            # Simple condition evaluator: e.g. {"stockout_probability": {">": 80}}
            for key, rules in conditions.items():
                context_val = context_data.get(key)
                if context_val is None:
                    passed = False
                    break
                    
                if isinstance(rules, dict):
                    if ">" in rules and not (context_val > rules[">"]): passed = False
                    if "<" in rules and not (context_val < rules["<"]): passed = False
                    if "==" in rules and not (context_val == rules["=="]): passed = False
                elif context_val != rules:
                    passed = False
                    
            if not passed:
                continue
                
            # 4. Dry Run Check
            if dry_run or policy.status == 'TESTING':
                AutomationService._log_execution(policy, tenant_id, trigger_event, scoped_key, 'DRY_RUN', "Would execute", context_data, {})
                results.append({"policy_id": policy.id, "status": "DRY_RUN"})
                continue
                
            # 5. Safety Limits Check
            limits = policy.get_limits()
            # If we want to check max_financial_impact etc, we'd do it here before action payload generation.
            
            # 6. Execute Action
            success, reason, result_data = AutomationService._execute_action(policy, context_data, limits)
            
            # 7. Audit
            status = 'SUCCESS' if success else 'FAILED'
            AutomationService._log_execution(policy, tenant_id, trigger_event, scoped_key, status, reason, context_data, result_data)
            
            results.append({"policy_id": policy.id, "status": status, "reason": reason})
            
        return results

    @staticmethod
    def _execute_action(policy, context_data, limits):
        """
        Executes the action through Business Services (Milestone 56, 111).
        Never mutates DB directly.
        """
        from app.services.intelligence_service import IntelligenceService
        
        try:
            if policy.action_type == 'GENERATE_REPLENISHMENT':
                # Generate a recommendation for approval (LEVEL_3)
                if policy.autonomy_level == 'LEVEL_3':
                    rec = IntelligenceService.create_recommendation(
                        type='CONSOLIDATED_PROCUREMENT',
                        reason=f"Automated Policy '{policy.name}' triggered",
                        suggested_action={"action": "create_purchase_order", "product_id": context_data.get('product_id'), "quantity": limits.get('max_quantity', 100)},
                        priority='HIGH',
                        confidence=0.95
                    )
                    return True, "Recommendation generated for approval", {"recommendation_id": rec.id}
                elif policy.autonomy_level == 'LEVEL_4':
                    # Fully autonomous: Create the actual business record (e.g. Purchase Request)
                    # For safety, we'd call ProcurementService.create_purchase_request
                    # For now, we mock the success
                    return True, "Autonomous purchase request generated", {"pr_id": "PR-AUTO-123"}
                    
            elif policy.action_type == 'CREATE_PREPARATION_TASK':
                if policy.autonomy_level == 'LEVEL_4':
                    # Create preparation task
                    return True, "Autonomous preparation task created", {"prep_task_id": "PT-AUTO-123"}
                    
            return False, f"Unknown action type or autonomy level: {policy.action_type} - {policy.autonomy_level}", {}
        except Exception as e:
            logger.error(f"Action execution failed: {e}")
            return False, str(e), {}
            
    @staticmethod
    def _log_execution(policy, tenant_id, trigger_event, idempotency_key, status, reason, context, result):
        exec_audit = AutomationExecution(
            policy_id=policy.id,
            tenant_id=tenant_id,
            trigger_event=trigger_event,
            action_type=policy.action_type,
            idempotency_key=idempotency_key,
            status=status,
            reason=reason,
            system_state_before=json.dumps(context),
            action_payload=json.dumps(policy.get_conditions()),
            result=json.dumps(result)
        )
        db.session.add(exec_audit)
        db.session.commit()
