from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np


def _stability_score(values: List[float]) -> float:
    if len(values) < 3:
        return 0.0
    std = float(np.std(values))
    return max(0.0, min(100.0, 100.0 - std * 220.0))


def _rhythm_score(values: List[float]) -> float:
    if len(values) < 5:
        return 0.0
    diff = np.diff(values)
    smooth = float(np.std(diff))
    return max(0.0, min(100.0, 100.0 - smooth * 180.0))


def _quality_level(score: float) -> str:
    if score >= 85:
        return "优秀"
    if score >= 70:
        return "良好"
    if score >= 55:
        return "合格"
    return "需改进"


def _pick_person_bbox(frame: np.ndarray, hog: cv2.HOGDescriptor) -> Optional[Tuple[int, int, int, int]]:
    rects, _ = hog.detectMultiScale(frame, winStride=(8, 8), padding=(8, 8), scale=1.05)
    if len(rects) == 0:
        return None
    x, y, w, h = max(rects, key=lambda r: r[2] * r[3])
    return int(x), int(y), int(w), int(h)


def analyze_video_pose(video_path: str, frame_stride: int = 3, max_frames: int = 360) -> Dict:
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError("无法打开视频文件，请检查格式是否受支持")

    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 640)
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 480)

    hog = cv2.HOGDescriptor()
    hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

    processed = 0
    detected = 0
    frame_idx = 0

    prev_gray = None
    prev_center = None

    rows = []
    center_x_arr = []
    center_y_arr = []
    motion_energy_arr = []
    bbox_ratio_arr = []

    while cap.isOpened() and processed < max_frames:
        ret, frame = cap.read()
        if not ret:
            break

        frame_idx += 1
        if frame_idx % max(1, frame_stride) != 0:
            continue

        processed += 1
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        bbox = _pick_person_bbox(frame, hog)
        has_person = bbox is not None

        if has_person:
            detected += 1
            x, y, w, h = bbox
            center_x = (x + w / 2.0) / max(width, 1)
            center_y = (y + h / 2.0) / max(height, 1)
            bbox_area = (w * h) / max(width * height, 1)
            bbox_ratio = w / max(h, 1)
        else:
            if prev_center is None:
                center_x = 0.5
                center_y = 0.5
            else:
                center_x, center_y = prev_center
            bbox_area = 0.0
            bbox_ratio = 0.0

        motion_dx = 0.0
        motion_dy = 0.0
        motion_energy = 0.0
        if prev_gray is not None:
            flow = cv2.calcOpticalFlowFarneback(
                prev_gray,
                gray,
                None,
                pyr_scale=0.5,
                levels=3,
                winsize=15,
                iterations=3,
                poly_n=5,
                poly_sigma=1.2,
                flags=0,
            )
            fx, fy = flow[..., 0], flow[..., 1]
            mag = np.sqrt(fx * fx + fy * fy)
            motion_energy = float(np.mean(mag))
            motion_dx = float(np.mean(fx))
            motion_dy = float(np.mean(fy))

        prev_gray = gray
        prev_center = (center_x, center_y)

        center_x_arr.append(center_x)
        center_y_arr.append(center_y)
        motion_energy_arr.append(motion_energy)
        bbox_ratio_arr.append(bbox_ratio)

        rows.append({
            "frame_index": frame_idx,
            "timestamp_s": round(frame_idx / fps, 3),
            "motion_energy": round(motion_energy, 4),
            "center_x": round(center_x, 4),
            "center_y": round(center_y, 4),
            "bbox_area": round(float(bbox_area), 4),
            "bbox_ratio": round(float(bbox_ratio), 4),
            "motion_dx": round(motion_dx, 5),
            "motion_dy": round(motion_dy, 5),
            "has_person": bool(has_person),
        })

    cap.release()

    if processed == 0:
        raise RuntimeError("视频帧为空，无法分析")

    detect_rate = detected / max(processed, 1)
    center_stability = _stability_score(center_y_arr)
    rhythm = _rhythm_score(motion_energy_arr)
    lateral_balance = max(0.0, min(100.0, 100.0 - abs(float(np.mean(center_x_arr) - 0.5)) * 260.0))
    movement_control = max(0.0, min(100.0, 100.0 - float(np.std(motion_energy_arr)) * 140.0))
    posture_consistency = _stability_score(bbox_ratio_arr)

    overall = (
        0.30 * center_stability
        + 0.20 * rhythm
        + 0.20 * lateral_balance
        + 0.20 * movement_control
        + 0.10 * posture_consistency
    )
    overall = max(0.0, min(100.0, float(overall)))

    suggestions = []
    if detect_rate < 0.35:
        suggestions.append("人体检测率偏低，建议使用正面、全身入镜、背景干净的视频。")
    if center_stability < 70:
        suggestions.append("纵向重心稳定性一般，建议加强沉胯与核心控制训练。")
    if rhythm < 70:
        suggestions.append("动作节奏波动较大，建议使用口令节拍进行分段练习。")
    if lateral_balance < 70:
        suggestions.append("横向位移偏离明显，建议增加步型稳定与中线控制训练。")
    if movement_control < 70:
        suggestions.append("整体动作控制性不足，建议先慢练再提速。")
    if not suggestions:
        suggestions.append("动作表现较稳定，建议继续强化细节一致性与节奏表达。")

    return {
        "processed_frames": processed,
        "detected_frames": detected,
        "detect_rate": round(detect_rate * 100, 2),
        "stance_balance": round(lateral_balance, 2),
        "upper_balance": round(posture_consistency, 2),
        "stability": round(center_stability, 2),
        "rhythm": round(rhythm, 2),
        "shoulder_level": round(movement_control, 2),
        "overall_score": round(overall, 2),
        "overall_level": _quality_level(overall),
        "suggestions": suggestions,
        "frames": rows,
    }
