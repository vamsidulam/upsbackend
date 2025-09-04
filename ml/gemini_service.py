import os
import google.genai as genai
from typing import Dict, List, Any
import logging
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv('atlas.env')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GeminiAIService:
    """Service for generating detailed UPS failure reasons using Google's Gemini AI (Gemini 2.0+)"""

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.client = None

        if not self.api_key:
            logger.warning("GEMINI_API_KEY not found in environment variables")
            return

        try:
            self.client = genai.Client(api_key=self.api_key)
            self.model_name = "gemini-1.5-flash"
            self.max_retries = 3
            logger.info("Gemini AI client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini AI client: {e}")
            self.client = None

    def generate_failure_reasons(self, ups_data: Dict[str, Any], prediction_data: Dict[str, Any]) -> List[str]:
        """Generate detailed failure reasons using Gemini AI"""
        if not self.client:
            return self._generate_fallback_reasons(ups_data, prediction_data)

        try:
            probability_failure = prediction_data.get('probability_failure', 0)
            ups_id = ups_data.get('upsId', 'Unknown')
            context = self._build_context(ups_data, prediction_data)

            prompt = f"""
            You are an expert UPS system analyst. Analyze the UPS data and generate 4-6 detailed, technical failure reasons.

            UPS ID: {ups_id}
            Failure Probability: {probability_failure:.1%}

            Current Metrics:
            {context}

            Generate specific reasons including:
            1. Exact values from the metrics
            2. Technical explanation
            3. Impact assessment
            4. Urgency level
            5. Recommended actions

            Focus on:
            - Overload conditions (>80% load)
            - Overheating (>40°C)
            - Power imbalance
            - Battery degradation
            - Efficiency issues
            - Voltage regulation
            - Component stress

            Start each reason with 🚨, ⚠️, or ℹ️.
            """

            for attempt in range(self.max_retries):
                try:
                    response = self.client.models.generate_content(
                        model=self.model_name,
                        prompt=prompt
                    )
                    if response and hasattr(response, "content") and response.content:
                        reasons = self._parse_gemini_response(response.content)
                        logger.info(f"Generated {len(reasons)} failure reasons (attempt {attempt + 1})")
                        return reasons
                    else:
                        logger.warning(f"Empty response from Gemini AI (attempt {attempt + 1})")
                except Exception as e:
                    logger.warning(f"Gemini AI attempt {attempt + 1} failed: {e}")
                    if attempt == self.max_retries - 1:
                        logger.error("All Gemini AI attempts failed, using fallback")
                        break
                    time.sleep(2 ** attempt)

            return self._generate_fallback_reasons(ups_data, prediction_data)

        except Exception as e:
            logger.error(f"Error generating failure reasons: {e}")
            return self._generate_fallback_reasons(ups_data, prediction_data)

    def _build_context(self, ups_data: Dict[str, Any], prediction_data: Dict[str, Any]) -> str:
        """Build context string for Gemini AI prompt"""
        context_parts = []

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

        power_input = ups_data.get('powerInput')
        power_output = ups_data.get('powerOutput')
        if power_input and power_output:
            power_balance = power_input - power_output
            power_efficiency = (power_output / power_input * 100) if power_input > 0 else 0
            context_parts.append(f"• Power Balance: {power_balance}W")
            context_parts.append(f"• Power Efficiency: {power_efficiency:.1f}%")
            if abs(power_balance) > 50:
                context_parts.append(f"• ⚠️ Power Imbalance: {abs(power_balance)}W indicates regulation issues")
            if power_efficiency < 85:
                context_parts.append(f"• ⚠️ Low Power Efficiency: {power_efficiency:.1f}% indicates component stress")

        load = ups_data.get('load')
        if load:
            if load > 90:
                context_parts.append(f"• 🚨 Critical Load: {load}% exceeds safe limits")
            elif load > 80:
                context_parts.append(f"• ⚠️ High Load: {load}% approaching capacity")
            elif load < 20:
                context_parts.append(f"• ℹ️ Low Load: {load}% may indicate inefficient operation")

        temperature = ups_data.get('temperature')
        if temperature:
            if temperature > 50:
                context_parts.append(f"• 🚨 Critical Temperature: {temperature}°C exceeds safe limits")
            elif temperature > 45:
                context_parts.append(f"• ⚠️ High Temperature: {temperature}°C approaching critical")
            elif temperature > 40:
                context_parts.append(f"• ℹ️ Elevated Temperature: {temperature}°C above optimal")

        battery_level = ups_data.get('batteryLevel')
        if battery_level:
            if battery_level < 30:
                context_parts.append(f"• 🚨 Critical Battery: {battery_level}% severe degradation")
            elif battery_level < 50:
                context_parts.append(f"• ⚠️ Low Battery: {battery_level}% shows aging")
            elif battery_level < 70:
                context_parts.append(f"• ℹ️ Battery Wear: {battery_level}% normal aging")

        voltage_input = ups_data.get('voltageInput')
        voltage_output = ups_data.get('voltageOutput')
        if voltage_input and voltage_output:
            voltage_diff = abs(voltage_input - voltage_output)
            if voltage_diff > 10:
                context_parts.append(f"• ⚠️ Voltage Regulation: {voltage_diff}V difference indicates issues")

        confidence = prediction_data.get('confidence', 0)
        if confidence > 0:
            context_parts.append(f"• ML Confidence: {confidence:.1%}")

        return "\n".join(context_parts) if context_parts else "No specific metrics available"

    def _parse_gemini_response(self, response_text: str) -> List[str]:
        """Parse Gemini AI response into failure reasons"""
        reasons = []
        lines = response_text.strip().split('\n')
        for line in lines:
            line = line.strip()
            if line and (line.startswith('🚨') or line.startswith('⚠️') or line.startswith('ℹ️')):
                reasons.append(line)
        if not reasons:
            reasons.append(response_text.strip())
        return reasons[:6]

    def _generate_fallback_reasons(self, ups_data: Dict[str, Any], prediction_data: Dict[str, Any]) -> List[str]:
        """Fallback failure reasons when Gemini AI is unavailable"""
        reasons = []
        probability_failure = prediction_data.get('probability_failure', 0)
        battery_level = ups_data.get('batteryLevel')
        temperature = ups_data.get('temperature')
        load = ups_data.get('load')
        power_input = ups_data.get('powerInput')
        power_output = ups_data.get('powerOutput')
        efficiency = ups_data.get('efficiency')

        # Battery
        if battery_level is not None:
            if battery_level < 30:
                reasons.append(f"🚨 Battery critically low at {battery_level}% - immediate replacement needed")
            elif battery_level < 50:
                reasons.append(f"⚠️ Battery low at {battery_level}% - schedule maintenance")
        
        # Temperature
        if temperature is not None:
            if temperature > 45:
                reasons.append(f"⚠️ High temperature at {temperature}°C - check cooling system")
        
        # Load
        if load is not None:
            if load > 90:
                reasons.append(f"⚠️ High load at {load}% - reduce load or add capacity")
        
        # Power balance
        if power_input and power_output:
            if abs(power_input - power_output) > 50:
                reasons.append(f"⚠️ Power imbalance of {power_input - power_output}W - electrical inspection required")

        # Efficiency
        if efficiency and efficiency < 85:
            reasons.append(f"⚠️ Low efficiency at {efficiency}% - check power conversion components")
        
        # ML probability
        if probability_failure > 0.6:
            reasons.append(f"⚠️ Elevated failure probability: {probability_failure:.1%}")
        
        return reasons[:6]
