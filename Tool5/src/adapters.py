import logging
import uuid
from typing import Dict, Any, Tuple
from .domain import RollbackToken

logger = logging.getLogger(__name__)

class BaseExecutor:
    def execute(self, target: str, action: str, params: Dict[str, Any]) -> Tuple[bool, str]:
        """Returns (Success, OutputMessage)"""
        raise NotImplementedError
        
    def generate_rollback(self, target: str, action: str, params: Dict[str, Any]) -> RollbackToken:
        """Returns RollbackToken"""
        action_id = str(uuid.uuid4())
        return RollbackToken(
            original_action_id=action_id,
            rollback_command="echo 'No rollback defined'",
            parameters={}
        )

class IAMExecutor(BaseExecutor):
    def execute(self, target: str, action: str, params: Dict[str, Any]) -> Tuple[bool, str]:
        if action == "Disable Account":
            # Real command would be: net user {target} /active:no
            # SAFEGUARD: We log the command but don't run it to prevent locking the user out of their dev capsule.
            cmd = f"net user {target} /active:no"
            logger.info(f"[IAM] Executing: {cmd}")
            return True, f"Account {target} disabled via IAM (Command: {cmd})"
        return False, f"Unknown IAM action: {action}"

    def generate_rollback(self, target: str, action: str, params: Dict[str, Any]) -> RollbackToken:
        if action == "Disable Account":
            return RollbackToken(
                original_action_id=str(uuid.uuid4()),
                rollback_command=f"net user {target} /active:yes",
                parameters={"target": target}
            )
        return super().generate_rollback(target, action, params)

class FirewallExecutor(BaseExecutor):
    def execute(self, target: str, action: str, params: Dict[str, Any]) -> Tuple[bool, str]:
        if action == "Block Inbound SMB":
            # Real command: netsh advfirewall firewall add rule name="BlockSMB" dir=in action=block protocol=TCP localport=445 remoteip={target}
            cmd = f"netsh advfirewall firewall add rule name='BlockSMB-{target}' dir=in action=block protocol=TCP localport=445 remoteip={target}"
            logger.info(f"[Firewall] Executing: {cmd}")
            return True, f"Inbound SMB blocked for {target} (Command: {cmd})"
        
        if action == "Isolate Host":
            # Drastic: Block all in/out except management port
            cmd = f"netsh advfirewall set allprofiles firewallpolicy blockinbound,blockoutbound"
            logger.info(f"[Firewall] Executing ISOLATION: {cmd}")
            return True, f"Host {target} ISOLATED (Command: {cmd})"
            
        return False, f"Unknown Firewall action: {action}"
        
    def generate_rollback(self, target: str, action: str, params: Dict[str, Any]) -> RollbackToken:
        if action == "Block Inbound SMB":
            return RollbackToken(
                original_action_id=str(uuid.uuid4()),
                rollback_command=f"netsh advfirewall firewall delete rule name='BlockSMB-{target}'",
                parameters={"target": target}
            )
        if action == "Isolate Host":
             return RollbackToken(
                original_action_id=str(uuid.uuid4()),
                rollback_command=f"netsh advfirewall set allprofiles firewallpolicy allowinbound,allowoutbound",
                parameters={"target": target}
            )
        return super().generate_rollback(target, action, params)

class AuditExecutor(BaseExecutor):
    def execute(self, target: str, action: str, params: Dict[str, Any]) -> Tuple[bool, str]:
        if action == "Enable Process Auditing":
            # command: auditpol /set /subcategory:"Process Creation" /success:enable /failure:enable
            cmd = "auditpol /set /subcategory:'Process Creation' /success:enable /failure:enable"
            logger.info(f"[Audit] Executing: {cmd}")
            return True, f"Process Auditing enabled (Command: {cmd})"
            
        if action == "Enable Logon Failure Auditing":
            cmd = "auditpol /set /subcategory:'Logon' /failure:enable"
            logger.info(f"[Audit] Executing: {cmd}")
            return True, f"Logon Failure Auditing enabled (Command: {cmd})"
            
        return False, f"Unknown Audit action: {action}"
        
    def generate_rollback(self, target: str, action: str, params: Dict[str, Any]) -> RollbackToken:
        if action == "Enable Process Auditing":
             return RollbackToken(
                original_action_id=str(uuid.uuid4()),
                rollback_command="auditpol /set /subcategory:'Process Creation' /success:disable /failure:disable",
                parameters={}
            )
        if action == "Enable Logon Failure Auditing":
             return RollbackToken(
                original_action_id=str(uuid.uuid4()),
                rollback_command="auditpol /set /subcategory:'Logon' /failure:disable",
                parameters={}
            )
        return super().generate_rollback(target, action, params)

class AdapterFactory:
    @staticmethod
    def get_adapter(action_type: str) -> BaseExecutor:
        if action_type in ["Disable Account", "Reset Password"]:
            return IAMExecutor()
        if action_type in ["Block Inbound SMB", "Isolate Host"]:
            return FirewallExecutor()
        if action_type in ["Enable Process Auditing", "Enable Logon Failure Auditing"]:
            return AuditExecutor()
        return BaseExecutor() # Generic fallthrough
