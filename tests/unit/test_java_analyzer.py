"""Tests for JavaAnalyzer."""

import pytest
from pathlib import Path
from src.core.analyzers.java_analyzer import JavaAnalyzer
from src.models.domain import LanguageType


@pytest.fixture
def java_analyzer():
    """Create JavaAnalyzer instance."""
    return JavaAnalyzer()


@pytest.fixture
def sample_spring_controller(tmp_path):
    """Create a sample Spring Boot controller."""
    java_code = """
package com.example.demo.controller;

import org.springframework.web.bind.annotation.*;
import com.example.demo.model.User;

@RestController
@RequestMapping("/api/users")
public class UserController {
    
    @GetMapping("/{id}")
    public User getUser(@PathVariable Long id) {
        return userService.findById(id);
    }
    
    @PostMapping
    public User createUser(@RequestBody User user) {
        return userService.save(user);
    }
    
    @DeleteMapping("/{id}")
    public void deleteUser(@PathVariable Long id) {
        userService.delete(id);
    }
}
"""
    file_path = tmp_path / "UserController.java"
    file_path.write_text(java_code)
    return file_path


@pytest.fixture
def sample_jpa_entity(tmp_path):
    """Create a sample JPA entity."""
    java_code = """
package com.example.demo.model;

import javax.persistence.*;

@Entity
@Table(name = "users")
public class User {
    
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @Column(name = "username")
    private String username;
    
    @Column(name = "email")
    private String email;
    
    // Getters and setters
}
"""
    file_path = tmp_path / "User.java"
    file_path.write_text(java_code)
    return file_path


def test_can_analyze_java_files(java_analyzer, tmp_path):
    """Test that JavaAnalyzer can identify .java files."""
    java_file = tmp_path / "Test.java"
    java_file.write_text("public class Test {}")
    
    assert java_analyzer.can_analyze(java_file)


def test_cannot_analyze_non_java_files(java_analyzer, tmp_path):
    """Test that JavaAnalyzer rejects non-.java files."""
    py_file = tmp_path / "test.py"
    py_file.write_text("print('hello')")
    
    assert not java_analyzer.can_analyze(py_file)


def test_extract_classes(java_analyzer, sample_spring_controller):
    """Test extraction of class names."""
    analysis = java_analyzer.analyze_file(sample_spring_controller)
    
    assert analysis.language == LanguageType.JAVA
    assert "UserController" in analysis.classes


def test_extract_methods(java_analyzer, sample_spring_controller):
    """Test extraction of method names."""
    analysis = java_analyzer.analyze_file(sample_spring_controller)
    
    # Should find methods like UserController.getUser
    method_names = [m.split('.')[-1] if '.' in m else m for m in analysis.functions]
    assert "getUser" in method_names or any("getUser" in m for m in analysis.functions)
    assert "createUser" in method_names or any("createUser" in m for m in analysis.functions)


def test_detect_spring_endpoints(java_analyzer, sample_spring_controller):
    """Test detection of Spring Boot endpoints."""
    analysis = java_analyzer.analyze_file(sample_spring_controller)
    
    # Should detect mapped endpoints
    assert len(analysis.endpoints) > 0
    
    # Check for specific endpoint
    get_endpoints = [e for e in analysis.endpoints if e.get("annotation") == "GetMapping"]
    assert len(get_endpoints) > 0


def test_detect_jpa_entities(java_analyzer, sample_jpa_entity):
    """Test detection of JPA entities."""
    analysis = java_analyzer.analyze_file(sample_jpa_entity)
    
    # Should detect User entity
    assert "User" in analysis.database_calls


def test_syntax_error_handling(java_analyzer, tmp_path):
    """Test handling of syntax errors."""
    invalid_java = tmp_path / "Invalid.java"
    invalid_java.write_text("public class Invalid { this is invalid syntax }")
    
    analysis = java_analyzer.analyze_file(invalid_java)
    
    # Should return partial analysis with error
    assert analysis.language == LanguageType.JAVA
    assert analysis.error is not None
    assert "Syntax error" in analysis.error


def test_line_count(java_analyzer, sample_spring_controller):
    """Test line counting."""
    analysis = java_analyzer.analyze_file(sample_spring_controller)
    
    assert analysis.lines > 0


def test_complexity_calculation(java_analyzer, sample_spring_controller):
    """Test complexity calculation."""
    analysis = java_analyzer.analyze_file(sample_spring_controller)
    
    # Should have some complexity
    assert analysis.complexity >= 1
