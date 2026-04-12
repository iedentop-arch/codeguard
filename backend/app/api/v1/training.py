"""
入驻培训 API
"""
import random
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.api.v1.auth import get_current_user
from app.models.models import ExamQuestion, VendorMember
from app.schemas.response import ApiResponse

router = APIRouter()


@router.get("/progress")
async def get_training_progress(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """获取入驻进度"""
    # TODO: 实现真实的进度追踪
    return ApiResponse(data={
        "current_step": 1,
        "steps": [
            {"step": 0, "label": "完善信息", "completed": True},
            {"step": 1, "label": "规范学习", "completed": False, "progress": "3/10"},
            {"step": 2, "label": "在线考试", "completed": False},
            {"step": 3, "label": "获取认证", "completed": False},
        ],
    })


@router.post("/mark-read/{spec_id}")
async def mark_spec_read(
    spec_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """标记规范已读"""
    return ApiResponse(message="已标记为已读")


@router.get("/exam/questions")
async def get_exam_questions(
    count: int = Query(10, ge=5, le=20),
    vendor_type: str = Query("B"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """获取考试题目"""
    result = await db.execute(
        select(ExamQuestion).where(
            ExamQuestion.is_active == True,
            ExamQuestion.vendor_types.contains(vendor_type)
        )
    )
    all_questions = result.scalars().all()
    
    # 随机抽取指定数量
    if len(all_questions) < count:
        selected = all_questions
    else:
        selected = random.sample(list(all_questions), count)
    
    return ApiResponse(data=[
        {
            "id": q.id,
            "category": q.category,
            "rule_id": q.rule_id,
            "severity": q.severity,
            "question_type": q.question_type,
            "question_text": q.question_text,
            "code_snippet": q.code_snippet,
            "options": q.options,
        }
        for q in selected
    ])


@router.post("/exam/submit")
async def submit_exam(
    answers: dict,  # {question_id: answer}
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """提交考试答案"""
    # 获取题目
    question_ids = list(answers.keys())
    result = await db.execute(
        select(ExamQuestion).where(ExamQuestion.id.in_(question_ids))
    )
    questions = result.scalars().all()
    
    # 计算分数
    correct_count = 0
    results = []
    for q in questions:
        user_answer = answers.get(str(q.id))
        is_correct = user_answer == q.correct_answer
        if is_correct:
            correct_count += 1
        results.append({
            "question_id": q.id,
            "user_answer": user_answer,
            "correct_answer": q.correct_answer,
            "is_correct": is_correct,
            "explanation": q.explanation,
        })
    
    total = len(questions)
    score = int(correct_count / total * 100) if total > 0 else 0
    passed = score >= 80
    
    return ApiResponse(data={
        "score": score,
        "passed": passed,
        "correct_count": correct_count,
        "total": total,
        "results": results,
    })


@router.get("/exam/result")
async def get_exam_result(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """获取最新考试结果"""
    # TODO: 实现真实的结果查询
    return ApiResponse(data={
        "score": 80,
        "passed": True,
        "exam_date": datetime.utcnow().isoformat(),
    })


@router.get("/certificate")
async def get_certificate(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """获取认证信息"""
    return ApiResponse(data={
        "certification_id": f"CG-{datetime.utcnow().strftime('%Y%m%d')}-001",
        "vendor_type": "B",
        "issue_date": datetime.utcnow().strftime('%Y-%m-%d'),
        "status": "active",
    })