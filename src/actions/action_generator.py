"""
Module: actions.action_generator
Purpose: Generates actionable outputs (emails, agent tasks) from classified recommendations
Dependencies: Jinja2 for templating, classification models

This module transforms classified recommendations into concrete actions:
- Email templates for different stakeholder groups
- Agent task definitions for automated workflows
- Priority-based routing logic
- Batch action generation for scale

Classes:
    ActionGenerator: Main class for generating actions
    EmailTemplate: Email template container
    AgentTask: Agent task definition
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
import json

from src.classification.recommendation_classifier import (
    ClassificationResult,
    RecommendationCategory
)


class ActionType(Enum):
    """Types of actions that can be generated"""
    EMAIL_PARTNER = "email_partner"
    EMAIL_INTERNAL = "email_internal"
    AGENT_CALL_WORKERS = "agent_call_workers"
    AGENT_ADJUST_PRICING = "agent_adjust_pricing"
    AGENT_EXPAND_RADIUS = "agent_expand_radius"
    AGENT_RELAX_REQUIREMENTS = "agent_relax_requirements"
    DASHBOARD_ALERT = "dashboard_alert"
    MANUAL_REVIEW = "manual_review"


@dataclass
class EmailTemplate:
    """
    Email template container
    
    Attributes:
        to: Recipient email or role
        subject: Email subject line
        body: Email body (can include variables)
        priority: Email priority (high/normal/low)
        variables: Template variables to fill
        cc: CC recipients
        attachments: List of attachments to include
    """
    to: str
    subject: str
    body: str
    priority: str = "normal"
    variables: Dict[str, Any] = None
    cc: List[str] = None
    attachments: List[str] = None
    
    def render(self, **kwargs) -> Dict[str, Any]:
        """
        Render email with provided variables
        
        Args:
            **kwargs: Variables to substitute in template
            
        Returns:
            Rendered email dictionary
        """
        # Simple variable substitution (use Jinja2 for complex templates)
        rendered_body = self.body
        rendered_subject = self.subject
        
        for key, value in kwargs.items():
            placeholder = f"{{{key}}}"
            rendered_body = rendered_body.replace(placeholder, str(value))
            rendered_subject = rendered_subject.replace(placeholder, str(value))
        
        return {
            "to": self.to,
            "subject": rendered_subject,
            "body": rendered_body,
            "priority": self.priority,
            "cc": self.cc or [],
            "attachments": self.attachments or []
        }


@dataclass
class AgentTask:
    """
    Agent task definition
    
    Attributes:
        task_type: Type of agent task
        priority: Task priority
        parameters: Task-specific parameters
        deadline: When task should be completed
        company_id: Associated company
        metadata: Additional task metadata
    """
    task_type: ActionType
    priority: str
    parameters: Dict[str, Any]
    deadline: Optional[datetime] = None
    company_id: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API/storage"""
        return {
            "task_type": self.task_type.value,
            "priority": self.priority,
            "parameters": self.parameters,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "company_id": self.company_id,
            "metadata": self.metadata or {}
        }


class ActionGenerator:
    """
    Generates actionable outputs from classified recommendations
    
    This class contains the business logic for transforming
    classifications into concrete actions like emails and agent tasks.
    """
    
    def __init__(self):
        """Initialize action generator with templates"""
        self.logger = logging.getLogger(__name__)
        self.templates = self._load_templates()
        
    def _load_templates(self) -> Dict[str, EmailTemplate]:
        """
        Load email templates for different scenarios
        
        Returns:
            Dictionary of templates by key
        """
        return {
            "wage_adjustment_partner": EmailTemplate(
                to="{partner_email}",
                subject="Action Required: Wage Adjustment Needed for Better Fill Rates",
                body="""Dear {partner_name},

We've analyzed your recent shift fill rates and identified that wage competitiveness is impacting your ability to fill shifts.

Current situation:
- Your current rate: ${current_wage}/hour
- Recommended rate: ${recommended_wage}/hour
- Market average: ${market_average}/hour
- Current fill rate: {fill_rate}%

By adjusting your wage to the recommended rate, we estimate you could improve your fill rate by {estimated_improvement}%.

Would you like to:
1. Automatically adjust to the recommended rate
2. Discuss alternative solutions
3. Review detailed market data

Please respond within 24 hours to ensure your upcoming shifts are filled.

Best regards,
Instawork Team""",
                priority="high"
            ),
            
            "lead_time_education": EmailTemplate(
                to="{partner_email}",
                subject="Tip: Post Shifts Earlier for Better Fill Rates",
                body="""Dear {partner_name},

We noticed your shifts are being posted with only {current_lead_time} hours notice. Shifts posted with less than 24 hours notice have significantly lower fill rates.

Quick facts:
- Shifts posted 48+ hours early: 85% fill rate
- Shifts posted 24-48 hours early: 70% fill rate
- Shifts posted <24 hours early: 45% fill rate

Your recent performance:
- Average lead time: {current_lead_time} hours
- Fill rate: {fill_rate}%

Try posting your next shifts at least {recommended_lead_time} hours in advance and see the difference!

Need help scheduling further in advance? Reply to this email for tips.

Best regards,
Instawork Team""",
                priority="normal"
            ),
            
            "high_risk_workers_internal": EmailTemplate(
                to="ops-team@instawork.com",
                subject="URGENT: High-Risk Workers Assigned - Company {company_id}",
                body="""High-risk workers have been assigned to upcoming shifts for {company_name}.

Shift Details:
- Shift ID: {shift_id}
- Start time: {shift_start}
- Location: {location}

High-Risk Workers Requiring Immediate Contact:
{worker_list}

Risk Factors:
{risk_factors}

Recommended Actions:
1. Call workers immediately to confirm attendance
2. Have backup workers on standby
3. Consider offering attendance bonus
4. Monitor check-in status closely

This is flagged as HIGH PRIORITY due to {risk_reason}.

Please update the tracking sheet once workers are contacted.""",
                priority="high",
                cc=["account-manager@instawork.com"]
            ),
            
            "geographic_expansion": EmailTemplate(
                to="{partner_email}",
                subject="Expand Your Worker Pool for Better Coverage",
                body="""Dear {partner_name},

Your shifts are attracting workers from an average distance of {avg_distance} miles, which is impacting fill rates.

Current situation:
- Average worker distance: {avg_distance} miles
- Workers >30 miles away: {distant_worker_percentage}%
- Current fill rate: {fill_rate}%

We recommend:
1. Expanding your search radius to {recommended_radius} miles
2. Considering transportation assistance
3. Adjusting shift times to accommodate commutes

Would you like us to automatically expand your worker pool? This could add {additional_workers} qualified workers.

Reply 'YES' to expand now, or 'CALL' to discuss options.

Best regards,
Instawork Team""",
                priority="normal"
            )
        }
    
    def generate_actions(
        self,
        company_id: str,
        classifications: List[ClassificationResult],
        company_context: Optional[Dict[str, Any]] = None
    ) -> Dict[ActionType, List[Any]]:
        """
        Generate all applicable actions for a company's classifications
        
        Args:
            company_id: Company identifier
            classifications: List of classified recommendations
            company_context: Additional company context
            
        Returns:
            Dictionary mapping action types to generated actions
        """
        actions = {
            ActionType.EMAIL_PARTNER: [],
            ActionType.EMAIL_INTERNAL: [],
            ActionType.AGENT_CALL_WORKERS: [],
            ActionType.AGENT_ADJUST_PRICING: [],
            ActionType.AGENT_EXPAND_RADIUS: [],
            ActionType.AGENT_RELAX_REQUIREMENTS: [],
            ActionType.DASHBOARD_ALERT: [],
            ActionType.MANUAL_REVIEW: []
        }
        
        context = company_context or {}
        
        # Process each classification
        for classification in classifications:
            generated = self._generate_single_action(
                company_id, 
                classification, 
                context
            )
            
            # Add generated actions to appropriate buckets
            for action_type, action in generated:
                actions[action_type].append(action)
        
        # Apply deduplication and priority logic
        actions = self._deduplicate_actions(actions)
        
        return actions
    
    def _generate_single_action(
        self,
        company_id: str,
        classification: ClassificationResult,
        context: Dict[str, Any]
    ) -> List[Tuple[ActionType, Any]]:
        """
        Generate action(s) for a single classification
        
        Args:
            company_id: Company identifier
            classification: Single classification result
            context: Company context
            
        Returns:
            List of (ActionType, action) tuples
        """
        actions = []
        
        # Route based on category and priority
        if classification.category == RecommendationCategory.WAGE_ADJUSTMENT:
            actions.extend(self._handle_wage_adjustment(
                company_id, classification, context
            ))
            
        elif classification.category == RecommendationCategory.LEAD_TIME:
            actions.extend(self._handle_lead_time(
                company_id, classification, context
            ))
            
        elif classification.category == RecommendationCategory.WORKER_QUALITY:
            actions.extend(self._handle_worker_quality(
                company_id, classification, context
            ))
            
        elif classification.category == RecommendationCategory.GEOGRAPHIC_EXPANSION:
            actions.extend(self._handle_geographic(
                company_id, classification, context
            ))
            
        elif classification.category == RecommendationCategory.REQUIREMENT_BARRIERS:
            actions.extend(self._handle_requirements(
                company_id, classification, context
            ))
            
        elif classification.category == RecommendationCategory.URGENT_ACTION:
            # Urgent actions get special handling
            actions.extend(self._handle_urgent(
                company_id, classification, context
            ))
        
        # Add dashboard alert for all high priority items
        if classification.action_priority == "HIGH":
            actions.append((
                ActionType.DASHBOARD_ALERT,
                {
                    "company_id": company_id,
                    "alert_type": classification.category.value,
                    "message": classification.specific_action,
                    "priority": "high",
                    "timestamp": datetime.utcnow().isoformat()
                }
            ))
        
        return actions
    
    def _handle_wage_adjustment(
        self,
        company_id: str,
        classification: ClassificationResult,
        context: Dict[str, Any]
    ) -> List[Tuple[ActionType, Any]]:
        """
        Handle wage adjustment recommendations
        
        Returns list of actions for wage-related issues
        """
        actions = []
        values = classification.extracted_values
        
        # Generate partner email
        if "wage_amounts" in values and len(values["wage_amounts"]) >= 2:
            current_wage = values["wage_amounts"][0]
            recommended_wage = values["wage_amounts"][1]
            
            # Only send email if adjustment is significant (>5%)
            if recommended_wage > current_wage * 1.05:
                email = self.templates["wage_adjustment_partner"].render(
                    partner_email=context.get("partner_email", "partner@company.com"),
                    partner_name=context.get("partner_name", "Partner"),
                    current_wage=current_wage,
                    recommended_wage=recommended_wage,
                    market_average=context.get("market_average", recommended_wage),
                    fill_rate=context.get("fill_rate", "Unknown"),
                    estimated_improvement=round((recommended_wage - current_wage) / current_wage * 100)
                )
                actions.append((ActionType.EMAIL_PARTNER, email))
            
            # Create automated pricing adjustment task
            if classification.action_priority == "HIGH":
                task = AgentTask(
                    task_type=ActionType.AGENT_ADJUST_PRICING,
                    priority="high",
                    parameters={
                        "company_id": company_id,
                        "current_rate": current_wage,
                        "target_rate": recommended_wage,
                        "auto_approve_threshold": 1.10,  # Auto-approve if <10% increase
                        "requires_approval": recommended_wage > current_wage * 1.10
                    },
                    deadline=datetime.utcnow() + timedelta(hours=24),
                    company_id=company_id
                )
                actions.append((ActionType.AGENT_ADJUST_PRICING, task.to_dict()))
        
        return actions
    
    def _handle_lead_time(
        self,
        company_id: str,
        classification: ClassificationResult,
        context: Dict[str, Any]
    ) -> List[Tuple[ActionType, Any]]:
        """
        Handle lead time recommendations
        
        Returns list of actions for lead time issues
        """
        actions = []
        values = classification.extracted_values
        
        # Send educational email
        if "hours" in values:
            current_lead = min(values["hours"])
            recommended_lead = max(values["hours"]) if len(values["hours"]) > 1 else 48
            
            email = self.templates["lead_time_education"].render(
                partner_email=context.get("partner_email", "partner@company.com"),
                partner_name=context.get("partner_name", "Partner"),
                current_lead_time=current_lead,
                recommended_lead_time=recommended_lead,
                fill_rate=context.get("fill_rate", "Unknown")
            )
            actions.append((ActionType.EMAIL_PARTNER, email))
        
        return actions
    
    def _handle_worker_quality(
        self,
        company_id: str,
        classification: ClassificationResult,
        context: Dict[str, Any]
    ) -> List[Tuple[ActionType, Any]]:
        """
        Handle worker quality/risk recommendations
        
        Returns list of actions for worker-related issues
        """
        actions = []
        values = classification.extracted_values
        
        # High priority internal alert
        if "worker_ids" in values and values["worker_ids"]:
            # Format worker list for email
            worker_list = "\n".join([
                f"- Worker {wid}: {context.get(f'worker_{wid}_name', 'Unknown')} "
                f"(Score: {context.get(f'worker_{wid}_score', 'N/A')}, "
                f"Distance: {context.get(f'worker_{wid}_distance', 'N/A')} miles)"
                for wid in values["worker_ids"]
            ])
            
            email = self.templates["high_risk_workers_internal"].render(
                company_id=company_id,
                company_name=context.get("company_name", f"Company {company_id}"),
                shift_id=context.get("shift_id", "Multiple"),
                shift_start=context.get("shift_start", "Various"),
                location=context.get("location", "Unknown"),
                worker_list=worker_list,
                risk_factors=context.get("risk_factors", "Low reliability scores"),
                risk_reason=classification.original_recommendation
            )
            actions.append((ActionType.EMAIL_INTERNAL, email))
            
            # Create call task for each worker
            for worker_id in values["worker_ids"]:
                task = AgentTask(
                    task_type=ActionType.AGENT_CALL_WORKERS,
                    priority="high",
                    parameters={
                        "worker_id": worker_id,
                        "company_id": company_id,
                        "reason": "pre_shift_confirmation",
                        "script_type": "high_risk_confirmation",
                        "backup_needed": True
                    },
                    deadline=datetime.utcnow() + timedelta(hours=2),
                    company_id=company_id
                )
                actions.append((ActionType.AGENT_CALL_WORKERS, task.to_dict()))
        
        return actions
    
    def _handle_geographic(
        self,
        company_id: str,
        classification: ClassificationResult,
        context: Dict[str, Any]
    ) -> List[Tuple[ActionType, Any]]:
        """
        Handle geographic/distance recommendations
        
        Returns list of actions for geographic issues
        """
        actions = []
        values = classification.extracted_values
        
        # Send expansion email
        if "miles" in values:
            current_radius = min(values["miles"])
            recommended_radius = max(values["miles"])
            
            email = self.templates["geographic_expansion"].render(
                partner_email=context.get("partner_email", "partner@company.com"),
                partner_name=context.get("partner_name", "Partner"),
                avg_distance=current_radius,
                distant_worker_percentage=context.get("distant_percentage", 40),
                fill_rate=context.get("fill_rate", "Unknown"),
                recommended_radius=recommended_radius,
                additional_workers=context.get("additional_workers", "50-100")
            )
            actions.append((ActionType.EMAIL_PARTNER, email))
            
            # Create radius expansion task
            task = AgentTask(
                task_type=ActionType.AGENT_EXPAND_RADIUS,
                priority="medium",
                parameters={
                    "company_id": company_id,
                    "current_radius": current_radius,
                    "target_radius": recommended_radius,
                    "auto_expand": classification.action_priority == "HIGH"
                },
                company_id=company_id
            )
            actions.append((ActionType.AGENT_EXPAND_RADIUS, task.to_dict()))
        
        return actions
    
    def _handle_requirements(
        self,
        company_id: str,
        classification: ClassificationResult,
        context: Dict[str, Any]
    ) -> List[Tuple[ActionType, Any]]:
        """
        Handle requirement barrier recommendations
        
        Returns list of actions for requirement issues
        """
        actions = []
        
        # Create requirement review task
        task = AgentTask(
            task_type=ActionType.AGENT_RELAX_REQUIREMENTS,
            priority=classification.action_priority.lower(),
            parameters={
                "company_id": company_id,
                "current_requirements": context.get("requirements", {}),
                "recommendation": classification.specific_action,
                "impact_analysis_needed": True
            },
            company_id=company_id
        )
        actions.append((ActionType.AGENT_RELAX_REQUIREMENTS, task.to_dict()))
        
        # Add manual review for significant changes
        if classification.confidence < 0.7:
            actions.append((
                ActionType.MANUAL_REVIEW,
                {
                    "company_id": company_id,
                    "review_type": "requirement_change",
                    "recommendation": classification.original_recommendation,
                    "confidence": classification.confidence
                }
            ))
        
        return actions
    
    def _handle_urgent(
        self,
        company_id: str,
        classification: ClassificationResult,
        context: Dict[str, Any]
    ) -> List[Tuple[ActionType, Any]]:
        """
        Handle urgent/critical recommendations
        
        Returns list of immediate actions
        """
        actions = []
        
        # All urgent actions get internal email
        email_body = f"""URGENT ACTION REQUIRED

Company: {context.get('company_name', company_id)}
Issue: {classification.original_recommendation}

Immediate action needed: {classification.specific_action}

This was flagged as URGENT with {classification.confidence:.0%} confidence.

Please take action within the next hour."""
        
        internal_email = {
            "to": "urgent-response@instawork.com",
            "subject": f"URGENT: {company_id} - Immediate Action Required",
            "body": email_body,
            "priority": "high",
            "cc": ["ops-manager@instawork.com", "account-manager@instawork.com"]
        }
        actions.append((ActionType.EMAIL_INTERNAL, internal_email))
        
        # Create high-priority manual review
        actions.append((
            ActionType.MANUAL_REVIEW,
            {
                "company_id": company_id,
                "review_type": "urgent_intervention",
                "recommendation": classification.original_recommendation,
                "deadline": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
                "escalation_required": True
            }
        ))
        
        return actions
    
    def _deduplicate_actions(
        self,
        actions: Dict[ActionType, List[Any]]
    ) -> Dict[ActionType, List[Any]]:
        """
        Remove duplicate actions and apply priority logic
        
        Args:
            actions: Dictionary of actions by type
            
        Returns:
            Deduplicated actions
        """
        # For emails, keep only highest priority per recipient
        if actions[ActionType.EMAIL_PARTNER]:
            seen_recipients = {}
            deduped_emails = []
            
            for email in actions[ActionType.EMAIL_PARTNER]:
                recipient = email.get("to")
                priority = email.get("priority", "normal")
                
                if recipient not in seen_recipients or \
                   self._priority_rank(priority) > self._priority_rank(seen_recipients[recipient]):
                    seen_recipients[recipient] = priority
                    deduped_emails.append(email)
            
            actions[ActionType.EMAIL_PARTNER] = deduped_emails
        
        # For agent tasks, merge similar tasks
        for task_type in [
            ActionType.AGENT_CALL_WORKERS,
            ActionType.AGENT_ADJUST_PRICING,
            ActionType.AGENT_EXPAND_RADIUS
        ]:
            if actions[task_type]:
                actions[task_type] = self._merge_similar_tasks(actions[task_type])
        
        return actions
    
    def _priority_rank(self, priority: str) -> int:
        """Convert priority string to numeric rank"""
        return {"low": 1, "normal": 2, "high": 3}.get(priority, 0)
    
    def _merge_similar_tasks(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Merge similar tasks to avoid duplication
        
        Args:
            tasks: List of task dictionaries
            
        Returns:
            Merged task list
        """
        # Group by company_id
        by_company = {}
        for task in tasks:
            company_id = task.get("company_id")
            if company_id not in by_company:
                by_company[company_id] = []
            by_company[company_id].append(task)
        
        # Merge tasks for same company
        merged = []
        for company_id, company_tasks in by_company.items():
            if len(company_tasks) == 1:
                merged.append(company_tasks[0])
            else:
                # Merge parameters and take highest priority
                merged_task = company_tasks[0].copy()
                for task in company_tasks[1:]:
                    # Take highest priority
                    if self._priority_rank(task.get("priority", "normal")) > \
                       self._priority_rank(merged_task.get("priority", "normal")):
                        merged_task["priority"] = task["priority"]
                    
                    # Merge parameters
                    if "parameters" in task:
                        merged_task["parameters"].update(task["parameters"])
                
                merged.append(merged_task)
        
        return merged
    
    def generate_batch_summary(
        self,
        all_actions: Dict[str, Dict[ActionType, List[Any]]]
    ) -> Dict[str, Any]:
        """
        Generate summary of actions across entire batch
        
        Args:
            all_actions: Actions for all companies
            
        Returns:
            Summary statistics and prioritized action list
        """
        summary = {
            "total_companies": len(all_actions),
            "total_actions": 0,
            "actions_by_type": {},
            "high_priority_companies": [],
            "email_queue_size": 0,
            "agent_task_queue_size": 0
        }
        
        # Count actions by type
        for action_type in ActionType:
            summary["actions_by_type"][action_type.value] = 0
        
        # Process each company's actions
        for company_id, company_actions in all_actions.items():
            company_total = 0
            has_high_priority = False
            
            for action_type, actions in company_actions.items():
                count = len(actions)
                summary["actions_by_type"][action_type.value] += count
                company_total += count
                
                # Check for high priority actions
                for action in actions:
                    if isinstance(action, dict) and action.get("priority") == "high":
                        has_high_priority = True
                    
                # Count emails and tasks
                if action_type in [ActionType.EMAIL_PARTNER, ActionType.EMAIL_INTERNAL]:
                    summary["email_queue_size"] += count
                elif action_type.value.startswith("agent_"):
                    summary["agent_task_queue_size"] += count
            
            summary["total_actions"] += company_total
            
            if has_high_priority:
                summary["high_priority_companies"].append(company_id)
        
        # Add execution estimates
        summary["estimated_email_send_time"] = f"{summary['email_queue_size'] * 0.5:.1f} minutes"
        summary["estimated_agent_task_time"] = f"{summary['agent_task_queue_size'] * 2:.1f} minutes"
        
        return summary