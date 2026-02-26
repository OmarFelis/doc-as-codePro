"""Tests for TypeScriptAnalyzer."""

import pytest
from pathlib import Path
from src.core.analyzers.typescript_analyzer import TypeScriptAnalyzer
from src.models.domain import LanguageType


@pytest.fixture
def ts_analyzer():
    """Create TypeScriptAnalyzer instance."""
    return TypeScriptAnalyzer()


@pytest.fixture
def sample_nestjs_controller(tmp_path):
    """Create a sample NestJS controller."""
    ts_code = """
import { Controller, Get, Post, Body, Param } from '@nestjs/common';
import { UserService } from './user.service';

@Controller('users')
export class UserController {
    constructor(private readonly userService: UserService) {}
    
    @Get(':id')
    async getUser(@Param('id') id: string): Promise<User> {
        return this.userService.findOne(id);
    }
    
    @Post()
    async createUser(@Body() createUserDto: CreateUserDto): Promise<User> {
        return this.userService.create(createUserDto);
    }
}
"""
    file_path = tmp_path / "user.controller.ts"
    file_path.write_text(ts_code)
    return file_path


@pytest.fixture
def sample_angular_component(tmp_path):
    """Create a sample Angular component."""
    ts_code = """
import { Component, OnInit } from '@angular/core';
import { UserService } from './user.service';

@Component({
    selector: 'app-user-list',
    templateUrl: './user-list.component.html',
    styleUrls: ['./user-list.component.css']
})
export class UserListComponent implements OnInit {
    users: User[] = [];
    
    constructor(private userService: UserService) {}
    
    ngOnInit(): void {
        this.loadUsers();
    }
    
    async loadUsers(): Promise<void> {
        this.users = await this.userService.getAll();
    }
}
"""
    file_path = tmp_path / "user-list.component.ts"
    file_path.write_text(ts_code)
    return file_path


@pytest.fixture
def sample_ts_interfaces(tmp_path):
    """Create a sample TypeScript file with interfaces and types."""
    ts_code = """
export interface User {
    id: string;
    name: string;
    email: string;
}

export type UserId = string | number;

export type UserRole = 'admin' | 'user' | 'guest';

export class UserRepository {
    async findById(id: UserId): Promise<User | null> {
        return null;
    }
    
    async save(user: User): Promise<void> {
        // Implementation
    }
}
"""
    file_path = tmp_path / "types.ts"
    file_path.write_text(ts_code)
    return file_path


def test_can_analyze_ts_files(ts_analyzer, tmp_path):
    """Test that TypeScriptAnalyzer can identify .ts files."""
    ts_file = tmp_path / "test.ts"
    ts_file.write_text("const x: number = 5;")
    
    assert ts_analyzer.can_analyze(ts_file)


def test_can_analyze_tsx_files(ts_analyzer, tmp_path):
    """Test that TypeScriptAnalyzer can identify .tsx files."""
    tsx_file = tmp_path / "test.tsx"
    tsx_file.write_text("const x = <div>Hello</div>;")
    
    assert ts_analyzer.can_analyze(tsx_file)


def test_cannot_analyze_non_ts_files(ts_analyzer, tmp_path):
    """Test that TypeScriptAnalyzer rejects non-TS files."""
    js_file = tmp_path / "test.js"
    js_file.write_text("console.log('hello');")
    
    assert not ts_analyzer.can_analyze(js_file)


def test_extract_classes(ts_analyzer, sample_nestjs_controller):
    """Test extraction of class names."""
    analysis = ts_analyzer.analyze_file(sample_nestjs_controller)
    
    assert analysis.language == LanguageType.TYPESCRIPT
    assert "UserController" in analysis.classes


def test_extract_interfaces(ts_analyzer, sample_ts_interfaces):
    """Test extraction of interfaces."""
    analysis = ts_analyzer.analyze_file(sample_ts_interfaces)
    
    # Interfaces are marked with (interface) suffix
    interface_items = [c for c in analysis.classes if "(interface)" in c]
    assert len(interface_items) > 0
    assert any("User" in i for i in interface_items)


def test_extract_types(ts_analyzer, sample_ts_interfaces):
    """Test extraction of type aliases."""
    analysis = ts_analyzer.analyze_file(sample_ts_interfaces)
    
    # Types are marked with (type) suffix
    type_items = [c for c in analysis.classes if "(type)" in c]
    assert len(type_items) > 0


def test_extract_functions(ts_analyzer, sample_angular_component):
    """Test extraction of functions/methods."""
    analysis = ts_analyzer.analyze_file(sample_angular_component)
    
    # Should find methods
    assert len(analysis.functions) > 0


def test_detect_nestjs_endpoints(ts_analyzer, sample_nestjs_controller):
    """Test detection of NestJS endpoints."""
    analysis = ts_analyzer.analyze_file(sample_nestjs_controller)
    
    # Should detect NestJS routes
    nestjs_endpoints = [e for e in analysis.endpoints if e.get("framework") == "nestjs"]
    assert len(nestjs_endpoints) > 0


def test_detect_angular_component(ts_analyzer, sample_angular_component):
    """Test detection of Angular components."""
    analysis = ts_analyzer.analyze_file(sample_angular_component)
    
    # Should detect Angular component
    angular_components = [e for e in analysis.endpoints if e.get("framework") == "angular"]
    assert len(angular_components) > 0


def test_extract_imports(ts_analyzer, sample_nestjs_controller):
    """Test extraction of imports."""
    analysis = ts_analyzer.analyze_file(sample_nestjs_controller)
    
    assert len(analysis.imports) > 0
    assert any("@nestjs/common" in imp for imp in analysis.imports)


def test_line_count(ts_analyzer, sample_nestjs_controller):
    """Test line counting."""
    analysis = ts_analyzer.analyze_file(sample_nestjs_controller)
    
    assert analysis.lines > 0


def test_complexity_calculation(ts_analyzer, sample_angular_component):
    """Test complexity calculation."""
    analysis = ts_analyzer.analyze_file(sample_angular_component)
    
    # Should have some complexity
    assert analysis.complexity >= 1
