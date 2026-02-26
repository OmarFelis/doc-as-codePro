"""Tests for JavaScriptAnalyzer."""

import pytest
from pathlib import Path
from src.core.analyzers.javascript_analyzer import JavaScriptAnalyzer
from src.models.domain import LanguageType


@pytest.fixture
def js_analyzer():
    """Create JavaScriptAnalyzer instance."""
    return JavaScriptAnalyzer()


@pytest.fixture
def sample_express_app(tmp_path):
    """Create a sample Express.js application."""
    js_code = """
const express = require('express');
const app = express();

app.get('/users', (req, res) => {
    res.json({ users: [] });
});

app.post('/users', (req, res) => {
    res.json({ success: true });
});

app.put('/users/:id', (req, res) => {
    res.json({ updated: true });
});

function getUserById(id) {
    return db.users.findOne({ id });
}

class UserService {
    async create(userData) {
        return await db.users.insert(userData);
    }
}

module.exports = { UserService, getUserById };
"""
    file_path = tmp_path / "app.js"
    file_path.write_text(js_code)
    return file_path


@pytest.fixture
def sample_es6_module(tmp_path):
    """Create a sample ES6 module."""
    js_code = """
import express from 'express';
import { Router } from 'express';

const router = Router();

export const getUsers = async () => {
    return await fetch('/api/users');
};

export class ApiClient {
    constructor(baseUrl) {
        this.baseUrl = baseUrl;
    }
    
    async get(endpoint) {
        return fetch(`${this.baseUrl}${endpoint}`);
    }
}

export default router;
"""
    file_path = tmp_path / "api.mjs"
    file_path.write_text(js_code)
    return file_path


def test_can_analyze_js_files(js_analyzer, tmp_path):
    """Test that JavaScriptAnalyzer can identify .js files."""
    js_file = tmp_path / "test.js"
    js_file.write_text("console.log('hello');")
    
    assert js_analyzer.can_analyze(js_file)


def test_can_analyze_mjs_files(js_analyzer, tmp_path):
    """Test that JavaScriptAnalyzer can identify .mjs files."""
    mjs_file = tmp_path / "test.mjs"
    mjs_file.write_text("console.log('hello');")
    
    assert js_analyzer.can_analyze(mjs_file)


def test_cannot_analyze_non_js_files(js_analyzer, tmp_path):
    """Test that JavaScriptAnalyzer rejects non-JS files."""
    py_file = tmp_path / "test.py"
    py_file.write_text("print('hello')")
    
    assert not js_analyzer.can_analyze(py_file)


def test_extract_functions(js_analyzer, sample_express_app):
    """Test extraction of function names."""
    analysis = js_analyzer.analyze_file(sample_express_app)
    
    assert analysis.language == LanguageType.JAVASCRIPT
    assert "getUserById" in analysis.functions


def test_extract_classes(js_analyzer, sample_express_app):
    """Test extraction of class names."""
    analysis = js_analyzer.analyze_file(sample_express_app)
    
    assert "UserService" in analysis.classes


def test_detect_express_routes(js_analyzer, sample_express_app):
    """Test detection of Express routes."""
    analysis = js_analyzer.analyze_file(sample_express_app)
    
    # Should detect Express routes
    assert len(analysis.endpoints) > 0
    
    # Check for specific route
    get_routes = [e for e in analysis.endpoints if e.get("http_method") == "GET"]
    assert len(get_routes) > 0


def test_extract_imports_es6(js_analyzer, sample_es6_module):
    """Test extraction of ES6 imports."""
    analysis = js_analyzer.analyze_file(sample_es6_module)
    
    assert "express" in analysis.imports


def test_parse_error_handling(js_analyzer, tmp_path):
    """Test handling of syntax errors."""
    invalid_js = tmp_path / "invalid.js"
    invalid_js.write_text("function test() { this is invalid }")
    
    analysis = js_analyzer.analyze_file(invalid_js)
    
    # Should return partial analysis with error
    assert analysis.language == LanguageType.JAVASCRIPT
    assert analysis.error is not None


def test_line_count(js_analyzer, sample_express_app):
    """Test line counting."""
    analysis = js_analyzer.analyze_file(sample_express_app)
    
    assert analysis.lines > 0


def test_complexity_calculation(js_analyzer, sample_express_app):
    """Test complexity calculation."""
    analysis = js_analyzer.analyze_file(sample_express_app)
    
    # Should have some complexity
    assert analysis.complexity >= 1
