"""Tests for the category store and models."""

import pytest
from src.models import Article, Category, Question, Evaluation, CategoryScore
from src.services.category_store import DEFAULT_CATEGORIES


def test_article_preview():
    a = Article(filename="test.md", content="Hello world " * 100)
    assert len(a.preview) <= 210
    assert a.preview.endswith("...")


def test_article_word_count():
    a = Article(filename="test.md", content="one two three four five")
    assert a.word_count == 5


def test_category_question_count():
    c = Category(name="Test", questions=[Question("Q1"), Question("Q2")])
    assert c.question_count == 2


def test_evaluation_score_labels():
    assert Evaluation(article_filename="x", overall_score=4.8).score_label == "Excellent"
    assert Evaluation(article_filename="x", overall_score=3.7).score_label == "Strong"
    assert Evaluation(article_filename="x", overall_score=2.5).score_label == "Moderate"
    assert Evaluation(article_filename="x", overall_score=1.5).score_label == "Weak"
    assert Evaluation(article_filename="x", overall_score=1.0).score_label == "Poor"


def test_default_categories_exist():
    assert len(DEFAULT_CATEGORIES) == 5
    for cat in DEFAULT_CATEGORIES:
        assert cat.question_count >= 3
        assert cat.name
        assert cat.description
