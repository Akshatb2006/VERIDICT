"""
Component Health Monitoring System for VERDICT
Tracks the health status of all verification components (FTSO, CMC API, FDC, Contract)
"""

from datetime import datetime, timedelta
from typing import Dict, Optional, List
import logging

logger = logging.getLogger(__name__)


class ComponentStatus:
    """Represents the status of a single component"""
    
    def __init__(self, name: str, component_type: str):
        self.name = name
        self.component_type = component_type
        self.status = "unknown"  # unknown, healthy, warning, offline, error
        self.last_check = None
        self.last_success = None
        self.error_message = None
        self.response_time_ms = None
        self.metadata = {}
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "name": self.name,
            "type": self.component_type,
            "status": self.status,
            "last_check": self.last_check.isoformat() if self.last_check else None,
            "last_success": self.last_success.isoformat() if self.last_success else None,
            "error_message": self.error_message,
            "response_time_ms": self.response_time_ms,
            "metadata": self.metadata
        }


class ComponentMonitor:
    """Monitor and track health of all VERDICT verification components"""
    
    def __init__(self, cmc_api=None, ftso_feed=None, flare_verifier=None):
        """
        Initialize the component monitor
        
        Args:
            cmc_api: CoinMarketCapAPI instance (optional)
            ftso_feed: FTSOPriceFeed instance (optional)
            flare_verifier: FlareVerifier instance (optional)
        """
        self.cmc_api = cmc_api
        self.ftso_feed = ftso_feed
        self.flare_verifier = flare_verifier
        
        # Component status tracking
        self.components = {
            "ftso_price_feed": ComponentStatus("FTSO Price Feed", "oracle"),
            "cmc_api": ComponentStatus("CMC API", "data_provider"),
            "fdc_endpoint": ComponentStatus("FDC Endpoint", "attestation"),
            "contract_log": ComponentStatus("Contract Log", "blockchain")
        }
        
        # Status history (keep last 100 status updates per component)
        self.status_history: Dict[str, List[Dict]] = {
            key: [] for key in self.components.keys()
        }
    
    async def check_ftso_health(self, token: str = "BTC") -> ComponentStatus:
        """
        Check FTSO price feed health
        
        Args:
            token: Token symbol to check (default: BTC)
            
        Returns:
            ComponentStatus for FTSO price feed
        """
        component = self.components["ftso_price_feed"]
        component.last_check = datetime.now()
        
        if not self.ftso_feed:
            component.status = "offline"
            component.error_message = "FTSO feed not initialized"
            return component
        
        try:
            start_time = datetime.now()
            price_result = await self.ftso_feed.get_price(token)
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            component.response_time_ms = round(response_time, 2)
            
            if price_result and price_result.price > 0:
                component.status = "healthy"
                component.last_success = datetime.now()
                component.error_message = None
                component.metadata = {
                    "price": price_result.price,
                    "token": token,
                    "timestamp": price_result.timestamp
                }
            else:
                component.status = "warning"
                component.error_message = "FTSO returned invalid price ($0)"
                
        except Exception as e:
            component.status = "error"
            component.error_message = f"FTSO check failed: {str(e)[:100]}"
            logger.error(f"[ComponentMonitor] FTSO health check failed: {e}")
        
        # Add to history
        self._add_to_history("ftso_price_feed", component.to_dict())
        return component
    
    def check_cmc_health(self, token: str = "BTC") -> ComponentStatus:
        """
        Check CoinMarketCap API health
        
        Args:
            token: Token symbol to check (default: BTC)
            
        Returns:
            ComponentStatus for CMC API
        """
        component = self.components["cmc_api"]
        component.last_check = datetime.now()
        
        if not self.cmc_api:
            component.status = "offline"
            component.error_message = "CMC API not initialized"
            return component
        
        try:
            start_time = datetime.now()
            market_data = self.cmc_api.get_token_info(token)
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            component.response_time_ms = round(response_time, 2)
            
            if market_data and 'price' in market_data:
                component.status = "healthy"
                component.last_success = datetime.now()
                component.error_message = None
                component.metadata = {
                    "price": market_data['price'],
                    "token": token,
                    "api_credits_used": market_data.get('credits_used', 'N/A')
                }
            else:
                component.status = "error"
                component.error_message = "CMC API returned invalid data"
                
        except Exception as e:
            component.status = "error"
            component.error_message = f"CMC API check failed: {str(e)[:100]}"
            logger.error(f"[ComponentMonitor] CMC health check failed: {e}")
        
        # Add to history
        self._add_to_history("cmc_api", component.to_dict())
        return component
    
    def check_fdc_health(self) -> ComponentStatus:
        """
        Check FDC (Flare Data Connector) endpoint health
        
        Returns:
            ComponentStatus for FDC endpoint
        """
        component = self.components["fdc_endpoint"]
        component.last_check = datetime.now()
        
        # For now, we simulate FDC status
        # In production, this would check actual FDC attestation availability
        try:
            # Check if we can reach the Flare network
            if self.flare_verifier and hasattr(self.flare_verifier, 'w3'):
                if self.flare_verifier.w3.is_connected():
                    component.status = "healthy"
                    component.last_success = datetime.now()
                    component.error_message = None
                    component.metadata = {
                        "network": "Coston2",
                        "connected": True
                    }
                else:
                    component.status = "offline"
                    component.error_message = "Cannot connect to Flare network"
            else:
                component.status = "warning"
                component.error_message = "FDC verification not fully configured"
                
        except Exception as e:
            component.status = "error"
            component.error_message = f"FDC check failed: {str(e)[:100]}"
            logger.error(f"[ComponentMonitor] FDC health check failed: {e}")
        
        # Add to history
        self._add_to_history("fdc_endpoint", component.to_dict())
        return component
    
    def check_contract_health(self) -> ComponentStatus:
        """
        Check smart contract verification system health
        
        Returns:
            ComponentStatus for contract log
        """
        component = self.components["contract_log"]
        component.last_check = datetime.now()
        
        if not self.flare_verifier:
            component.status = "offline"
            component.error_message = "Contract verifier not initialized"
            return component
        
        try:
            # Check contract connection
            if hasattr(self.flare_verifier, 'contract') and self.flare_verifier.contract:
                component.status = "healthy"
                component.last_success = datetime.now()
                component.error_message = None
                component.metadata = {
                    "contract_address": self.flare_verifier.contract_address,
                    "network": "Coston2"
                }
            else:
                component.status = "warning"
                component.error_message = "Contract not deployed or configured"
                
        except Exception as e:
            component.status = "error"
            component.error_message = f"Contract check failed: {str(e)[:100]}"
            logger.error(f"[ComponentMonitor] Contract health check failed: {e}")
        
        # Add to history
        self._add_to_history("contract_log", component.to_dict())
        return component
    
    async def check_all_components(self, token: str = "BTC") -> Dict[str, Dict]:
        """
        Check health of all components
        
        Args:
            token: Token symbol to check (default: BTC)
            
        Returns:
            Dictionary of all component statuses
        """
        logger.info(f"[ComponentMonitor] Checking all components for {token}")
        
        # Check all components
        await self.check_ftso_health(token)
        self.check_cmc_health(token)
        self.check_fdc_health()
        self.check_contract_health()
        
        # Calculate overall health
        overall_status = self._calculate_overall_status()
        
        result = {
            "components": {
                key: comp.to_dict() for key, comp in self.components.items()
            },
            "overall": overall_status,
            "timestamp": datetime.now().isoformat(),
            "summary": self._generate_summary()
        }
        
        return result
    
    def _calculate_overall_status(self) -> str:
        """
        Calculate overall system health based on component statuses
        
        Returns:
            Overall status: healthy, degraded, critical, offline
        """
        statuses = [comp.status for comp in self.components.values()]
        
        if all(s == "healthy" for s in statuses):
            return "healthy"
        elif any(s == "offline" or s == "error" for s in statuses):
            # If any critical component is offline, system is critical
            return "critical"
        elif any(s == "warning" for s in statuses):
            return "degraded"
        else:
            return "unknown"
    
    def _generate_summary(self) -> Dict:
        """
        Generate summary statistics
        
        Returns:
            Summary dictionary with counts and averages
        """
        statuses = [comp.status for comp in self.components.values()]
        
        return {
            "total_components": len(self.components),
            "healthy": sum(1 for s in statuses if s == "healthy"),
            "warning": sum(1 for s in statuses if s == "warning"),
            "error": sum(1 for s in statuses if s == "error" or s == "offline"),
            "avg_response_time_ms": self._calculate_avg_response_time()
        }
    
    def _calculate_avg_response_time(self) -> Optional[float]:
        """Calculate average response time across all components"""
        times = [
            comp.response_time_ms 
            for comp in self.components.values() 
            if comp.response_time_ms is not None
        ]
        
        if times:
            return round(sum(times) / len(times), 2)
        return None
    
    def _add_to_history(self, component_key: str, status_dict: Dict):
        """Add status to component history"""
        if component_key in self.status_history:
            self.status_history[component_key].append(status_dict)
            # Keep only last 100 entries
            if len(self.status_history[component_key]) > 100:
                self.status_history[component_key] = self.status_history[component_key][-100:]
    
    def get_component_history(self, component_key: str, limit: int = 10) -> List[Dict]:
        """
        Get recent history for a specific component
        
        Args:
            component_key: Component identifier
            limit: Number of recent entries to return
            
        Returns:
            List of status dictionaries
        """
        if component_key in self.status_history:
            return self.status_history[component_key][-limit:]
        return []
