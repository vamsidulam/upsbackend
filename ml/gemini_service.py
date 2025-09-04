import os
import google.genai as genai
from typing import Dict, List, Any
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv('atlas.env')

# Configure logging
logger = logging.getLogger(__name__)

class GeminiAIService:
    """Service for generating detailed failure reasons using Google's Gemini AI"""
    
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model = None
        
        if not self.api_key:
            logger.warning("GEMINI_API_KEY not found in environment variables")
            return
        
        try:
            # Configure Gemini AI with timeout and retry settings
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            self.timeout = 120  # Increased timeout to 120 seconds
            self.max_retries = 3  # Add retry mechanism
            logger.info("Gemini AI service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini AI service: {e}")
            self.model = None
    
    def generate_failure_reasons(self, ups_data: Dict[str, Any], prediction_data: Dict[str, Any]) -> List[str]:
        """Generate detailed failure reasons using Gemini AI"""
        if not self.model:
            return self._generate_fallback_reasons(ups_data, prediction_data)
        
        try:
            probability_failure = prediction_data.get('probability_failure', 0)
            ups_id = ups_data.get('upsId', 'Unknown')
            context = self._build_context(ups_data, prediction_data)
            
            prompt = f"""
            You are an expert UPS system analyst with deep knowledge of power systems, battery technology, and electrical engineering. Analyze this UPS data and generate 4-6 highly detailed, technical failure reasons that explain exactly why this UPS is at risk of failure.

            UPS ID: {ups_id}
            Failure Probability: {probability_failure:.1%}
            
            Current Metrics:
            {context}
            
            Generate specific, technical reasons explaining why this UPS is at risk. Each reason should include:
            1. **Exact values** from the metrics above
            2. **Technical explanation** of what's happening inside the UPS
            3. **Impact assessment** - what will happen if not addressed
            4. **Urgency level** - how soon action is needed
            5. **Specific recommended actions** - what to do to fix it
            
            Focus on these key failure modes:
            - **Overload conditions** (load > 80%)
            - **Overheating** (temperature > 40°C)
            - **Power imbalance** (input vs output mismatch)
            - **Battery degradation** (capacity loss, aging)
            - **Efficiency issues** (power conversion problems)
            - **Voltage regulation problems** (input/output voltage differences)
            - **Component stress** (capacitors, transformers, etc.)
            
            Use professional engineering language and start each reason with 🚨 (critical/immediate), ⚠️ (warning/urgent), or ℹ️ (info/monitor).
            
            Make each reason specific to the actual values provided, not generic statements.
            """
            
            # Try with retry logic
            for attempt in range(self.max_retries):
                try:
                    # Remove timeout parameter as it's not supported
                    response = self.model.generate_content(prompt)
                    
                    if response and response.text:
                        reasons = self._parse_gemini_response(response.text)
                        logger.info(f"Generated {len(reasons)} failure reasons using Gemini AI (attempt {attempt + 1})")
                        return reasons
                    else:
                        logger.warning(f"Empty response from Gemini AI (attempt {attempt + 1})")
                        
                except Exception as e:
                    logger.warning(f"Gemini AI attempt {attempt + 1} failed: {e}")
                    if attempt == self.max_retries - 1:  # Last attempt
                        logger.error(f"All Gemini AI attempts failed, using fallback")
                        break
                    # Wait before retry
                    import time
                    time.sleep(2 ** attempt)  # Exponential backoff
            
            # If all attempts failed, use fallback
            return self._generate_fallback_reasons(ups_data, prediction_data)
                
        except Exception as e:
            logger.error(f"Error generating failure reasons with Gemini AI: {e}")
            return self._generate_fallback_reasons(ups_data, prediction_data)
    
    def _build_context(self, ups_data: Dict[str, Any], prediction_data: Dict[str, Any]) -> str:
        """Build context string for Gemini AI prompt with enhanced analysis"""
        context_parts = []
        
        # Core metrics with analysis
        metrics = [
            ('batteryLevel', 'Battery Level', '%'),
            ('temperature', 'Temperature', '°C'),
            ('load', 'Load', '%'),
            ('efficiency', 'Efficiency', '%'),
            ('powerInput', 'Power Input', 'W'),
            ('powerOutput', 'Power Output', 'W'),
            ('voltageInput', 'Input Voltage', 'V'),
            ('voltageOutput', 'Output Voltage', 'V'),
            ('frequency', 'Frequency', 'Hz'),
            ('uptime', 'Runtime', ' hours'),
            ('capacity', 'Capacity', 'VA')
        ]
        
        for key, label, unit in metrics:
            value = ups_data.get(key)
            if value is not None:
                context_parts.append(f"• {label}: {value}{unit}")
        
        # Enhanced power analysis
        power_input = ups_data.get('powerInput')
        power_output = ups_data.get('powerOutput')
        if power_input is not None and power_output is not None:
            power_balance = power_input - power_output
            power_efficiency = (power_output / power_input * 100) if power_input > 0 else 0
            context_parts.append(f"• Power Balance: {power_balance}W")
            context_parts.append(f"• Power Efficiency: {power_efficiency:.1f}%")
            
            # Power stress analysis
            if abs(power_balance) > 50:
                context_parts.append(f"• ⚠️ Power Imbalance: {abs(power_balance)}W difference indicates electrical regulation issues")
            if power_efficiency < 85:
                context_parts.append(f"• ⚠️ Low Power Efficiency: {power_efficiency:.1f}% suggests internal losses and component stress")
        
        # Load stress analysis
        load = ups_data.get('load')
        if load is not None:
            if load > 90:
                context_parts.append(f"• 🚨 Critical Load: {load}% exceeds safe operating limits")
            elif load > 80:
                context_parts.append(f"• ⚠️ High Load: {load}% approaching capacity limits")
            elif load < 20:
                context_parts.append(f"• ℹ️ Low Load: {load}% may indicate inefficient operation")
        
        # Temperature stress analysis
        temperature = ups_data.get('temperature')
        if temperature is not None:
            if temperature > 50:
                context_parts.append(f"• 🚨 Critical Temperature: {temperature}°C exceeds safe limits")
            elif temperature > 45:
                context_parts.append(f"• ⚠️ High Temperature: {temperature}°C approaching critical levels")
            elif temperature > 40:
                context_parts.append(f"• ℹ️ Elevated Temperature: {temperature}°C above optimal range")
        
        # Battery health analysis
        battery_level = ups_data.get('batteryLevel')
        if battery_level is not None:
            if battery_level < 30:
                context_parts.append(f"• 🚨 Critical Battery: {battery_level}% indicates severe degradation")
            elif battery_level < 50:
                context_parts.append(f"• ⚠️ Low Battery: {battery_level}% shows accelerated aging")
            elif battery_level < 70:
                context_parts.append(f"• ℹ️ Battery Wear: {battery_level}% indicates normal aging")
        
        # Voltage regulation analysis
        voltage_input = ups_data.get('voltageInput')
        voltage_output = ups_data.get('voltageOutput')
        if voltage_input is not None and voltage_output is not None:
            voltage_diff = abs(voltage_input - voltage_output)
            if voltage_diff > 10:
                context_parts.append(f"• ⚠️ Voltage Regulation: {voltage_diff}V difference indicates regulation issues")
        
        # Add prediction confidence
        confidence = prediction_data.get('confidence', 0)
        if confidence > 0:
            context_parts.append(f"• ML Confidence: {confidence:.1%}")
        
        return "\n".join(context_parts) if context_parts else "No specific metrics available"
    
    def _parse_gemini_response(self, response_text: str) -> List[str]:
        """Parse Gemini AI response into individual failure reasons"""
        reasons = []
        lines = response_text.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if line and (line.startswith('•') or line.startswith('-') or line.startswith('🚨') or line.startswith('⚠️') or line.startswith('ℹ️')):
                reason = line.lstrip('•- ').strip()
                if reason:
                    reasons.append(reason)
        
        # Fallback parsing if bullet points not found
        if not reasons:
            parts = response_text.split('🚨')
            for part in parts[1:]:
                if part.strip():
                    reasons.append(f"🚨{part.strip()}")
            
            if not reasons:
                parts = response_text.split('⚠️')
                for part in parts[1:]:
                    if part.strip():
                        reasons.append(f"⚠️{part.strip()}")
        
        return reasons[:5]  # Limit to 5 reasons
    
    def _generate_fallback_reasons(self, ups_data: Dict[str, Any], prediction_data: Dict[str, Any]) -> List[str]:
        """Generate enhanced fallback failure reasons when Gemini AI is not available"""
        reasons = []
        probability_failure = prediction_data.get('probability_failure', 0)
        
        # Enhanced Battery analysis with specific technical details
        battery_level = ups_data.get('batteryLevel')
        if battery_level is not None:
            if battery_level < 20:
                reasons.append(f"🚨 CRITICAL BATTERY FAILURE IMMINENT: Battery level at {battery_level}% indicates severe degradation. The UPS will fail to provide backup power during outages, potentially causing immediate system shutdowns. Battery replacement is critical within 24 hours. The internal resistance has increased significantly, reducing the battery's ability to deliver current under load.")
            elif battery_level < 30:
                reasons.append(f"🚨 HIGH BATTERY FAILURE RISK: Battery level at {battery_level}% shows critical wear. The UPS may fail to sustain load during power interruptions, risking data loss and equipment damage. Schedule emergency battery replacement. The battery's capacity has dropped below 30% of original specification, indicating accelerated aging.")
            elif battery_level < 40:
                reasons.append(f"⚠️ MODERATE BATTERY FAILURE RISK: Battery level at {battery_level}% indicates accelerated aging. The UPS backup time is significantly reduced, increasing failure probability during extended outages. Plan battery replacement within 1 week. The battery is showing signs of sulfation and reduced charge retention.")
            elif battery_level < 60:
                reasons.append(f"ℹ️ ELEVATED BATTERY WEAR: Battery level at {battery_level}% shows normal aging but reduced backup capacity. Monitor closely as this accelerates failure risk during high-load conditions. The battery's internal resistance is increasing, reducing efficiency during discharge cycles.")
        
        # Enhanced Temperature analysis with component impact details
        temperature = ups_data.get('temperature')
        if temperature is not None:
            if temperature > 50:
                reasons.append(f"🚨 CRITICAL TEMPERATURE FAILURE IMMINENT: Temperature at {temperature}°C exceeds safe operating limits. This will cause immediate thermal shutdown to prevent component damage. The UPS will fail and cannot be restarted until cooled. Check cooling system immediately. High temperature is damaging electrolytic capacitors, reducing their lifespan and causing voltage regulation issues.")
            elif temperature > 45:
                reasons.append(f"⚠️ HIGH TEMPERATURE FAILURE RISK: Temperature at {temperature}°C is approaching critical limits. Prolonged exposure will damage internal components, capacitors, and reduce battery life. The UPS may fail unexpectedly during high-load operations. Inspect cooling system within 4 hours. The elevated temperature is accelerating the aging of electronic components and reducing overall system reliability.")
            elif temperature > 40:
                reasons.append(f"ℹ️ ELEVATED TEMPERATURE RISK: Temperature at {temperature}°C is above optimal range. This accelerates component aging and increases failure probability during peak loads. Monitor cooling efficiency and ensure proper ventilation. The temperature rise is causing increased stress on power semiconductors and reducing the efficiency of the power conversion process.")
        
        # Enhanced Load analysis with power stress details
        load = ups_data.get('load')
        if load is not None:
            if load > 95:
                reasons.append(f"🚨 CRITICAL LOAD FAILURE IMMINENT: Load at {load}% exceeds safe operating capacity. The UPS is operating beyond its design limits and will fail catastrophically, potentially causing immediate shutdown and equipment damage. Reduce load immediately or add additional UPS capacity. The power semiconductors are operating at maximum stress, increasing junction temperature and reducing reliability.")
            elif load > 90:
                reasons.append(f"⚠️ HIGH LOAD FAILURE RISK: Load at {load}% is approaching maximum capacity. The UPS is under significant stress, increasing heat generation and component wear. During power outages, the UPS may fail to sustain this load, causing system shutdowns. Consider load balancing or capacity upgrade. The high load is causing increased switching losses in the power conversion circuitry.")
            elif load > 80:
                reasons.append(f"ℹ️ ELEVATED LOAD MONITORING: Load at {load}% is above optimal range. While not immediately dangerous, this increases UPS stress and reduces backup time. Monitor closely during peak operations as this accelerates component aging. The elevated load is reducing the efficiency of the power conversion process and increasing thermal stress.")
        
        # Enhanced Power balance analysis
        power_input = ups_data.get('powerInput')
        power_output = ups_data.get('powerOutput')
        if power_input is not None and power_output is not None:
            power_balance = power_input - power_output
            if abs(power_balance) > 50:
                reasons.append(f"🚨 CRITICAL POWER IMBALANCE: Power imbalance of {power_balance}W indicates severe electrical problems. The UPS is not properly regulating power flow, which will cause voltage fluctuations and equipment damage. This requires immediate electrical inspection and repair. The large power difference suggests issues with the power factor correction circuitry or voltage regulation systems.")
            elif abs(power_balance) > 20:
                reasons.append(f"⚠️ MODERATE POWER IMBALANCE: Power imbalance of {power_balance}W shows electrical regulation issues. The UPS is not efficiently managing power distribution, increasing failure risk during load changes. Schedule electrical maintenance within 24 hours. The imbalance indicates inefficiencies in the power conversion process and potential issues with the output voltage regulation.")
        
        # Enhanced Efficiency analysis
        efficiency = ups_data.get('efficiency')
        if efficiency is not None:
            if efficiency < 80:
                reasons.append(f"🚨 CRITICAL EFFICIENCY ISSUE: Efficiency at {efficiency}% is critically low, indicating severe internal losses and component stress. The UPS is consuming excessive power and generating excessive heat, which will lead to premature failure. This requires immediate investigation of the power conversion circuitry and thermal management systems.")
            elif efficiency < 85:
                reasons.append(f"⚠️ LOW EFFICIENCY WARNING: Efficiency at {efficiency}% is below optimal levels, indicating increased internal losses and reduced performance. The UPS is consuming more power than necessary and generating additional heat. Schedule maintenance to inspect the power conversion components and cooling systems.")
        
        # If no specific reasons found, add probability-based general reasons with technical details
        if not reasons:
            if probability_failure > 0.8:
                reasons.append(f"🚨 CRITICAL FAILURE IMMINENT: ML model predicts {probability_failure:.1%} failure probability. The UPS is showing multiple critical failure indicators that will cause complete system failure within hours. This requires immediate emergency maintenance to prevent catastrophic equipment damage and data loss. Multiple component stress factors are converging, indicating systemic failure is imminent.")
            elif probability_failure > 0.6:
                reasons.append(f"⚠️ ELEVATED FAILURE RISK: ML model predicts {probability_failure:.1%} failure probability. The UPS is showing significant performance degradation that increases failure risk during high-load conditions or power disturbances. The system is operating outside optimal parameters, increasing stress on critical components.")
            elif probability_failure > 0.4:
                reasons.append(f"ℹ️ MODERATE FAILURE RISK: ML model predicts {probability_failure:.1%} failure probability. The UPS is showing early warning signs that, while not immediately critical, indicate increased failure probability over time. Early intervention can prevent escalation to critical failure conditions.")
        
        return reasons[:6]  # Limit to 6 reasons for enhanced analysis
