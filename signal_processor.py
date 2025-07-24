"""
Signal processing and aggregation module.
Processes individual indicator signals and creates consensus signals.
"""

import logging
from typing import Dict, List
from statistics import mean
from collections import Counter

class SignalProcessor:
    """Process and aggregate trading signals from multiple indicators."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Signal weights for different indicators
        self.signal_weights = {
            'RSI': 1.2,
            'MACD': 1.5,
            'Bollinger Bands': 1.0,
            'MA Crossover': 1.3,
            'Volume Analysis': 0.8,
            'Stochastic': 0.9,
            'Momentum': 0.7
        }
    
    def process_signals(self, signals: List[Dict]) -> Dict:
        """
        Process and aggregate multiple signals into a consensus signal.
        
        Args:
            signals: List of individual indicator signals
            
        Returns:
            Dict containing consensus signal with confidence and reasoning
        """
        if not signals:
            return {
                'signal': 'HOLD',
                'confidence': 0,
                'reason': 'No signals available',
                'individual_signals': []
            }
        
        try:
            # Filter out invalid signals
            valid_signals = [s for s in signals if s and 'signal' in s and 'confidence' in s]
            
            if not valid_signals:
                return {
                    'signal': 'HOLD', 
                    'confidence': 0,
                    'reason': 'No valid signals',
                    'individual_signals': []
                }
            
            # Calculate weighted consensus
            consensus = self._calculate_weighted_consensus(valid_signals)
            
            # Determine final signal based on consensus
            final_signal = self._determine_final_signal(consensus, valid_signals)
            
            return final_signal
            
        except Exception as e:
            self.logger.error(f"Error processing signals: {str(e)}")
            return {
                'signal': 'HOLD',
                'confidence': 0,
                'reason': f'Processing error: {str(e)}',
                'individual_signals': signals
            }
    
    def _calculate_weighted_consensus(self, signals: List[Dict]) -> Dict:
        """
        Calculate weighted consensus from individual signals.
        
        Args:
            signals: List of valid signals
            
        Returns:
            Dict with consensus metrics
        """
        buy_weight = 0
        sell_weight = 0
        hold_weight = 0
        total_confidence = 0
        total_weight = 0
        
        signal_reasons = []
        
        for signal in signals:
            signal_type = signal['signal']
            confidence = signal['confidence']
            source = signal.get('source', 'Unknown')
            reason = signal.get('reason', '')
            
            # Get weight for this signal source
            weight = self.signal_weights.get(source, 1.0)
            weighted_confidence = confidence * weight
            
            if signal_type == 'BUY':
                buy_weight += weighted_confidence
                signal_reasons.append(f"{source}: BUY ({confidence:.0f}%)")
            elif signal_type == 'SELL':
                sell_weight += weighted_confidence
                signal_reasons.append(f"{source}: SELL ({confidence:.0f}%)")
            else:  # HOLD
                hold_weight += weighted_confidence
                signal_reasons.append(f"{source}: HOLD ({confidence:.0f}%)")
            
            total_confidence += weighted_confidence
            total_weight += weight
        
        # Calculate average confidence
        avg_confidence = total_confidence / total_weight if total_weight > 0 else 0
        
        return {
            'buy_weight': buy_weight,
            'sell_weight': sell_weight,
            'hold_weight': hold_weight,
            'avg_confidence': avg_confidence,
            'signal_reasons': signal_reasons,
            'total_signals': len(signals)
        }
    
    def _determine_final_signal(self, consensus: Dict, signals: List[Dict]) -> Dict:
        """
        Determine the final trading signal based on consensus.
        
        Args:
            consensus: Consensus metrics
            signals: Original signals list
            
        Returns:
            Final signal dict
        """
        buy_weight = consensus['buy_weight']
        sell_weight = consensus['sell_weight']
        hold_weight = consensus['hold_weight']
        avg_confidence = consensus['avg_confidence']
        
        # Determine dominant signal
        if buy_weight > sell_weight and buy_weight > hold_weight:
            signal_type = 'BUY'
            confidence = min(100, buy_weight / (buy_weight + sell_weight + hold_weight) * 100)
        elif sell_weight > buy_weight and sell_weight > hold_weight:
            signal_type = 'SELL' 
            confidence = min(100, sell_weight / (buy_weight + sell_weight + hold_weight) * 100)
        else:
            signal_type = 'HOLD'
            confidence = max(avg_confidence, 50)  # At least 50% confidence for HOLD
        
        # Apply additional filters for signal quality
        confidence = self._apply_signal_filters(signal_type, confidence, signals)
        
        # Build reason string
        reason = self._build_reason_string(consensus, signal_type, confidence)
        
        return {
            'signal': signal_type,
            'confidence': round(confidence, 1),
            'reason': reason,
            'individual_signals': signals,
            'consensus_metrics': {
                'buy_weight': round(buy_weight, 1),
                'sell_weight': round(sell_weight, 1),
                'hold_weight': round(hold_weight, 1),
                'signal_count': consensus['total_signals']
            }
        }
    
    def _apply_signal_filters(self, signal_type: str, confidence: float, signals: List[Dict]) -> float:
        """
        Apply additional filters to adjust signal confidence.
        
        Args:
            signal_type: BUY/SELL/HOLD
            confidence: Base confidence score
            signals: Individual signals
            
        Returns:
            Adjusted confidence score
        """
        adjusted_confidence = confidence
        
        # Count signal types
        signal_types = [s['signal'] for s in signals if 'signal' in s]
        signal_counts = Counter(signal_types)
        
        # Penalize if there's too much disagreement
        total_signals = len(signal_types)
        if total_signals > 1:
            agreement_ratio = signal_counts.get(signal_type, 0) / total_signals
            
            if agreement_ratio < 0.6:  # Less than 60% agreement
                adjusted_confidence *= 0.8  # Reduce confidence by 20%
        
        # Boost confidence for strong technical confluences
        strong_indicators = ['RSI', 'MACD', 'MA Crossover']
        strong_signal_count = sum(1 for s in signals 
                                if s.get('source') in strong_indicators 
                                and s.get('signal') == signal_type
                                and s.get('confidence', 0) >= 75)
        
        if strong_signal_count >= 2:
            adjusted_confidence = min(100, adjusted_confidence * 1.1)  # Boost by 10%
        
        # Minimum confidence thresholds
        if signal_type in ['BUY', 'SELL']:
            adjusted_confidence = max(adjusted_confidence, 60)  # Minimum 60% for trade signals
        
        return adjusted_confidence
    
    def _build_reason_string(self, consensus: Dict, signal_type: str, confidence: float) -> str:
        """
        Build a human-readable reason string for the signal.
        
        Args:
            consensus: Consensus metrics
            signal_type: Final signal type
            confidence: Final confidence
            
        Returns:
            Reason string
        """
        signal_reasons = consensus['signal_reasons']
        total_signals = consensus['total_signals']
        
        # Create main reason
        if signal_type == 'BUY':
            main_reason = f"Bullish consensus from {total_signals} indicators"
        elif signal_type == 'SELL':
            main_reason = f"Bearish consensus from {total_signals} indicators"
        else:
            main_reason = f"Mixed signals from {total_signals} indicators"
        
        # Add top contributing signals
        contributing_signals = [r for r in signal_reasons if signal_type in r][:3]  # Top 3
        
        if contributing_signals:
            details = " | ".join(contributing_signals)
            reason = f"{main_reason}. {details}"
        else:
            reason = main_reason
        
        return reason
    
    def calculate_risk_metrics(self, signals: List[Dict], current_price: float) -> Dict:
        """
        Calculate risk metrics for the trading signal.
        
        Args:
            signals: Individual signals
            current_price: Current asset price
            
        Returns:
            Dict with risk metrics
        """
        try:
            # Default risk parameters
            default_stop_loss_pct = 0.02  # 2%
            default_take_profit_pct = 0.04  # 4%
            
            # Analyze signal strength for risk adjustment
            strong_signals = [s for s in signals if s.get('confidence', 0) >= 80]
            weak_signals = [s for s in signals if s.get('confidence', 0) < 60]
            
            # Adjust risk based on signal strength
            if len(strong_signals) >= 2:
                # Strong signals - can afford tighter stops
                stop_loss_pct = default_stop_loss_pct * 0.8
                take_profit_pct = default_take_profit_pct * 1.2
            elif len(weak_signals) > len(strong_signals):
                # Weak signals - wider stops
                stop_loss_pct = default_stop_loss_pct * 1.5
                take_profit_pct = default_take_profit_pct * 0.8
            else:
                # Default risk
                stop_loss_pct = default_stop_loss_pct
                take_profit_pct = default_take_profit_pct
            
            return {
                'stop_loss_pct': stop_loss_pct,
                'take_profit_pct': take_profit_pct,
                'risk_reward_ratio': take_profit_pct / stop_loss_pct,
                'position_size_suggestion': self._calculate_position_size(stop_loss_pct)
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating risk metrics: {str(e)}")
            return {
                'stop_loss_pct': 0.02,
                'take_profit_pct': 0.04,
                'risk_reward_ratio': 2.0,
                'position_size_suggestion': 'Medium'
            }
    
    def _calculate_position_size(self, stop_loss_pct: float) -> str:
        """
        Suggest position size based on stop loss percentage.
        
        Args:
            stop_loss_pct: Stop loss percentage
            
        Returns:
            Position size suggestion
        """
        if stop_loss_pct <= 0.015:  # <= 1.5%
            return 'Large'
        elif stop_loss_pct <= 0.025:  # <= 2.5%
            return 'Medium'
        else:  # > 2.5%
            return 'Small'
