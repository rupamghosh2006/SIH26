#!/usr/bin/env python3
"""
Debris Detection System for Website Integration
Clean, focused script for detecting threats using the trained YOLO model
"""

try:
    import cv2
except ImportError:
    cv2 = None

try:
    import numpy as np
except ImportError:
    np = None

try:
    from ultralytics import YOLO
except ImportError:
    YOLO = None

import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

class ThreatDetector:
    """
    Main debris detection class for website integration
    """
    
    def __init__(self, model_path: str = "best.pt", confidence_threshold: float = 0.5, verbose: bool = True):
        """
        Initialize the threat detector
        
        Args:
            model_path: Path to the trained YOLO model
            confidence_threshold: Minimum confidence for detections
            verbose: Whether to print status messages
        """
        self.model_path = model_path
        self.confidence_threshold = confidence_threshold
        self.verbose = verbose
        self.model = None
        self.class_names = {}
        self.load_model()
    
    def load_model(self) -> bool:
        """
        Load the YOLO model
        
        Returns:
            bool: True if model loaded successfully, False otherwise
        """
        try:
            if YOLO is None:
                if self.verbose:
                    print("ultralytics YOLO module not installed, running in acoustic shadow mode.")
                return False
            if not self.model_path or not os.path.exists(self.model_path):
                candidates = [
                    self.model_path,
                    "backend/models/yolov8_seaguard.pt",
                    os.path.join(os.path.dirname(__file__), "backend", "models", "yolov8_seaguard.pt"),
                    "backend/models/yolov8_varuna.pt",
                    "yolov8_seaguard.pt",
                    "best.pt",
                    "yolov8n.pt",
                    os.path.join(os.path.dirname(__file__), "yolov8n.pt"),
                ]
                found = False
                for cand in candidates:
                    if cand and os.path.exists(cand):
                        self.model_path = cand
                        found = True
                        break
                if not found:
                    if self.verbose:
                        print(f"No YOLO model checkpoint found, operating in acoustic shadow anomaly mode.")
                    return False
            
            self.model = YOLO(self.model_path)
            self.class_names = self.model.names
            
            if self.verbose:
                print(f"Threat detector initialized successfully using {self.model_path}")
                print(f"Model classes: {self.class_names}")
                print(f"Confidence threshold: {self.confidence_threshold}")
            
            return True
            
        except Exception as e:
            if self.verbose:
                print(f"Error loading model: {e}")
            return False
    
    def detect_threats(self, image_path: str) -> Dict:
        """
        Detect threats in an image (using YOLO or acoustic shadow fallback)
        """
        try:
            # Check if image exists
            if not os.path.exists(image_path):
                return {
                    'success': False,
                    'error': f'Image file not found: {image_path}',
                    'threats': [],
                    'metadata': {}
                }
            
            # Load image info
            if cv2 is not None:
                image = cv2.imread(image_path)
                height, width = image.shape[:2] if image is not None else (600, 800)
            else:
                image = None
                try:
                    from PIL import Image as PILImage
                    with PILImage.open(image_path) as pimg:
                        width, height = pimg.size
                except Exception:
                    width, height = 800, 600
            
            threats = []
            
            # If YOLO model is loaded, run YOLO inference
            if self.model:
                results = self.model(image_path, conf=self.confidence_threshold, iou=0.45, verbose=False)
                if results and len(results) > 0:
                    result = results[0]
                    if result.boxes is not None and len(result.boxes) > 0:
                        for box in result.boxes:
                            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                            confidence = float(box.conf[0].cpu().numpy())
                            class_id = int(box.cls[0].cpu().numpy())
                            class_name = self.class_names.get(class_id, f"target_{class_id}")
                            threat_level = self._calculate_threat_level(confidence, class_name)
                            threat = {
                                'id': len(threats) + 1,
                                'class': class_name,
                                'class_id': class_id,
                                'confidence': float(confidence),
                                'confidence_percentage': float(confidence * 100),
                                'threat_level': threat_level,
                                'bounding_box': {
                                    'x1': float(x1),
                                    'y1': float(y1),
                                    'x2': float(x2),
                                    'y2': float(y2),
                                    'width': float(x2 - x1),
                                    'height': float(y2 - y1),
                                    'center_x': float(x1 + (x2 - x1) / 2),
                                    'center_y': float(y1 + (y2 - y1) / 2)
                                },
                                'area_pixels': float((x2 - x1) * (y2 - y1)),
                                'relative_size': float(((x2 - x1) * (y2 - y1)) / (width * height) * 100)
                            }
                            threats.append(threat)
            
            # Fallback acoustic feature / anomaly detection ONLY if no deep learning model is loaded
            if self.model is None:
                threats = self._detect_acoustic_anomalies(image, width, height)
            
            overall_threat = self._assess_overall_threat(threats)
            return {
                'success': True,
                'threats': threats,
                'threat_count': len(threats),
                'overall_threat_level': overall_threat['level'],
                'overall_threat_score': overall_threat['score'],
                'metadata': {
                    'image_path': image_path,
                    'image_width': width,
                    'image_height': height,
                    'image_size_kb': round(os.path.getsize(image_path) / 1024, 2),
                    'model_used': self.model_path if self.model else "Varuna Acoustic Highlight-Shadow Pipeline",
                    'confidence_threshold': self.confidence_threshold,
                    'detection_timestamp': self._get_timestamp()
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Detection error: {str(e)}',
                'threats': [],
                'metadata': {}
            }

    def _detect_acoustic_anomalies(self, image, width: int, height: int) -> List[Dict]:
        """Physics-based acoustic highlight & shadow detector for Side-Scan Sonar imagery."""
        if cv2 is None or image is None:
            return []
        
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Detect high-intensity acoustic highlights (strong acoustic backscatter)
        mean_val, std_val = cv2.meanStdDev(blurred)
        thresh_high = float(mean_val[0][0] + 1.8 * std_val[0][0])
        _, high_mask = cv2.threshold(blurred, min(240, max(120, int(thresh_high))), 255, cv2.THRESH_BINARY)
        
        contours, _ = cv2.findContours(high_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        threats = []
        
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < (width * height * 0.0008) or area > (width * height * 0.35):
                continue
            
            x, y, w, h = cv2.boundingRect(cnt)
            aspect_ratio = float(w) / max(1, h)
            
            # Physics-based acoustic shadow verification:
            # In side-scan sonar, an elevated target blocks acoustic waves, casting a dark acoustic shadow
            # directly behind the highlight.
            shadow_verified = False
            sx = min(width - 1, x + w)
            sw = min(w * 2, width - sx)
            if sw > 5 and h > 5:
                shadow_roi = gray[y:min(height, y + h), sx:sx + sw]
                if shadow_roi.size > 0:
                    shadow_mean = float(cv2.mean(shadow_roi)[0])
                    if shadow_mean < mean_val[0][0] * 0.75:
                        shadow_verified = True
            
            # Physical geometry categorization
            if aspect_ratio > 3.0 or aspect_ratio < 0.33:
                cls_name = 'linear_debris'
            elif aspect_ratio > 1.3 and area > (width * height * 0.006):
                cls_name = 'ghost_net' if shadow_verified else 'acoustic_anomaly'
            elif area > (width * height * 0.04):
                cls_name = 'shipwreck' if shadow_verified else 'seabed_formation'
            elif 0.8 <= aspect_ratio <= 1.2 and area < (width * height * 0.015):
                cls_name = 'container_drum' if shadow_verified else 'acoustic_anomaly'
            else:
                cls_name = 'acoustic_anomaly'
            
            base_conf = 0.72 if shadow_verified else 0.55
            conf = min(0.88, max(0.45, base_conf + (area / (width * height * 0.05)) * 0.12))
            threat_level = self._calculate_threat_level(conf, cls_name)
            
            threats.append({
                'id': len(threats) + 1,
                'class': cls_name,
                'debris_type': cls_name,
                'class_id': 0,
                'confidence': float(conf),
                'confidence_percentage': float(round(conf * 100, 1)),
                'threat_level': threat_level,
                'ecological_risk': threat_level,
                'verification_status': 'shadow_verified' if shadow_verified else 'candidate_anomaly',
                'acoustic_shadow_verified': shadow_verified,
                'bounding_box': {
                    'x1': float(x),
                    'y1': float(y),
                    'x2': float(x + w),
                    'y2': float(y + h),
                    'width': float(w),
                    'height': float(h),
                    'center_x': float(x + w / 2),
                    'center_y': float(y + h / 2)
                },
                'area_pixels': float(w * h),
                'relative_size': float((w * h) / (width * height) * 100)
            })
            if len(threats) >= 10:
                break
        
        return threats
    
    def _calculate_threat_level(self, confidence: float, class_name: str) -> str:
        """
        Calculate ecological severity / hazard level based on debris type & confidence
        """
        debris_priorities = {
            'ghost_net': 4,              # Entanglement hazard to marine life & reefs
            'fishing_gear': 4,           # ALDFG risk
            'chain_or_debris': 4,        # Entanglement / cable hazard
            'container_drum': 3,         # Toxic / industrial hazard
            'metal_object': 3,           # Pipeline / navigation obstruction
            'propeller': 3,              # Metal propulsion debris
            'valve': 3,                  # Subsea pipe fitting
            'hook': 3,                   # Longline / marine hook
            'shipwreck': 3,              # Major structural wreck
            'tires': 2,                  # Rubber / microplastic pollution
            'tire': 2,                   # Rubber tire debris
            'bottle_or_container': 2,    # Synthetic plastic/glass debris
            'can': 2,                    # Metallic beverage container
            'linear_debris': 3,          # Cable, chain, or discarded pipe
            'acoustic_anomaly': 2,       # Unclassified high-backscatter target
            'unknown_anomaly': 2,        # Unclassified anomaly
            'rock_cluster': 1,           # Natural seabed geology
            'seabed_formation': 1,       # Natural geological seabed formation
            'wall_boundary': 1           # Tank or seabed boundary wall
        }
        
        priority = debris_priorities.get(class_name, 2)
        
        if confidence >= 0.8 and priority >= 3:
            return 'CRITICAL'
        elif confidence >= 0.65 and priority >= 2:
            return 'HIGH'
        elif confidence >= 0.5:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _assess_overall_threat(self, threats: List[Dict]) -> Dict:
        """
        Assess overall threat level based on all detections
        
        Args:
            threats: List of detected threats
            
        Returns:
            Dict: Overall threat assessment
        """
        if not threats:
            return {'level': 'NONE', 'score': 0.0}
        
        # Calculate weighted threat score
        total_score = 0.0
        threat_weights = {
            'CRITICAL': 4.0,
            'HIGH': 3.0,
            'MEDIUM': 2.0,
            'LOW': 1.0
        }
        
        for threat in threats:
            weight = threat_weights.get(threat['threat_level'], 1.0)
            total_score += threat['confidence'] * weight
        
        # Normalize score to 0-1 for threat-level classification
        max_possible_score = len(threats) * 4.0  # All critical threats
        normalized_score = total_score / max_possible_score if max_possible_score > 0 else 0.0
        
        # Determine overall threat level
        if normalized_score >= 0.8:
            level = 'CRITICAL'
        elif normalized_score >= 0.6:
            level = 'HIGH'
        elif normalized_score >= 0.4:
            level = 'MEDIUM'
        elif normalized_score >= 0.2:
            level = 'LOW'
        else:
            level = 'MINIMAL'
        
        # Return score as percentage so UI can display it directly.
        return {
            'level': level,
            'score': round(normalized_score * 100, 1)
        }
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def save_detection_result(self, result: Dict, output_path: str = None) -> str:
        """
        Save detection result as JSON
        
        Args:
            result: Detection result dictionary
            output_path: Path to save the result (optional)
            
        Returns:
            str: Path where result was saved
        """
        if output_path is None:
            timestamp = self._get_timestamp().replace(':', '-').replace(' ', '_')
            output_path = f"threat_detection_result_{timestamp}.json"
        
        try:
            with open(output_path, 'w') as f:
                json.dump(result, f, indent=2)
            
            if self.verbose:
                print(f"Detection result saved: {output_path}")
            return output_path
            
        except Exception as e:
            if self.verbose:
                print(f"Error saving result: {e}")
            return ""
    
    def create_annotated_image(self, image_path: str, result: Dict, output_path: str = None) -> str:
        """
        Create annotated image with debris detections
        
        Args:
            image_path: Path to original image
            result: Detection result dictionary
            output_path: Path to save annotated image (optional)
            
        Returns:
            str: Path where annotated image was saved
        """
        if not result['success'] or not result['threats']:
            return ""
        
        try:
            if cv2 is None:
                import shutil
                if output_path:
                    shutil.copy2(image_path, output_path)
                    return output_path
                return image_path
            
            # Load original image
            image = cv2.imread(image_path)
            if image is None:
                return ""
            
            # Draw bounding boxes and labels
            for threat in result['threats']:
                bbox = threat['bounding_box']
                x1, y1, x2, y2 = int(bbox['x1']), int(bbox['y1']), int(bbox['x2']), int(bbox['y2'])
                
                # Choose color based on threat level
                colors = {
                    'CRITICAL': (0, 0, 255),    # Red
                    'HIGH': (0, 165, 255),      # Orange
                    'MEDIUM': (0, 255, 255),    # Yellow
                    'LOW': (0, 255, 0)          # Green
                }
                color = colors.get(threat['threat_level'], (255, 255, 255))
                
                # Draw bounding box
                cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
                
                # Draw label
                label = f"{threat['class']} {threat['confidence_percentage']:.1f}%"
                label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
                cv2.rectangle(image, (x1, y1 - label_size[1] - 10), (x1 + label_size[0], y1), color, -1)
                cv2.putText(image, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            # Save annotated image
            if output_path is None:
                timestamp = self._get_timestamp().replace(':', '-').replace(' ', '_')
                output_path = f"threat_detection_annotated_{timestamp}.jpg"
            
            cv2.imwrite(output_path, image)
            if self.verbose:
                print(f"Annotated image saved: {output_path}")
            return output_path
            
        except Exception as e:
            if self.verbose:
                print(f"Error creating annotated image: {e}")
            return ""

def main():
    """
    Main function for testing the threat detector
    """
    print("=" * 60)
    print("DEBRIS DETECTION SYSTEM")
    print("=" * 60)
    
    # Initialize threat detector
    detector = ThreatDetector(confidence_threshold=0.3)  # Lower threshold for better detection
    
    if not detector.model:
        print("❌ Failed to initialize threat detector")
        return
    
    # Find test images
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
    all_files = [f for f in os.listdir('.') if os.path.isfile(f)]
    image_files = [f for f in all_files if any(f.lower().endswith(ext) for ext in image_extensions)]
    
    # Filter out result images and model files
    test_images = [f for f in image_files if not f.startswith('threat_') and 
                   not f.startswith('result_') and not f.startswith('comprehensive_') and 
                   f != 'best.pt']
    
    if not test_images:
        print("❌ No test images found")
        return
    
    print(f"📷 Found {len(test_images)} test image(s)")
    
    # Process each image
    for i, image_path in enumerate(test_images, 1):
        print(f"\n🔍 Processing image {i}: {Path(image_path).name}")
        print("-" * 50)
        
        # Detect threats
        result = detector.detect_threats(image_path)
        
        if result['success']:
            print(f"✅ Detection successful")
            print(f"🎯 Threats found: {result['threat_count']}")
            print(f"⚠️  Overall threat level: {result['overall_threat_level']}")
            print(f"📊 Threat score: {result['overall_threat_score']}%")
            
            if result['threats']:
                print(f"\n🚨 DETECTED THREATS:")
                for threat in result['threats']:
                    print(f"   • {threat['class']} - {threat['threat_level']} threat")
                    print(f"     Confidence: {threat['confidence_percentage']:.1f}%")
                    print(f"     Size: {threat['relative_size']:.1f}% of image")
            
            # Save results
            detector.save_detection_result(result)
            detector.create_annotated_image(image_path, result)
            
        else:
            print(f"❌ Detection failed: {result['error']}")
    
    print(f"\n{'='*60}")
    print("DEBRIS DETECTION COMPLETED")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
