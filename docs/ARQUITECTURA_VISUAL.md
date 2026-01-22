# 🏗️ ARQUITECTURA v3.0 - DIAGRAMA VISUAL

## 📊 Vista General del Sistema

```
┌─────────────────────────────────────────────────────────────────────┐
│                     DOC-AS-CODE SERVICE v3.0                        │
│                    Arquitectura Limpia y Modular                    │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │                               │
                    ▼                               ▼
        ┌─────────────────────┐         ┌─────────────────────┐
        │   CONFIGURATION     │         │      LOGGING        │
        │   (Pydantic)        │         │    (structlog)      │
        │                     │         │                     │
        │ • Settings          │         │ • JSON logs         │
        │ • Validation        │         │ • Context           │
        │ • .env loading      │         │ • Dev/Prod modes    │
        └─────────────────────┘         └─────────────────────┘
                    │
                    ▼
        ┌─────────────────────────────────────────────────────┐
        │              DOMAIN MODELS (Pydantic)               │
        ├─────────────────────────────────────────────────────┤
        │ • FileAnalysis      • ProjectAnalysis               │
        │ • Documentation     • PublishRequest                │
        │ • LanguageType      • AnalysisStatus                │
        │ • ComponentType     • PublishResponse               │
        └─────────────────────────────────────────────────────┘
                    │
                    ▼
        ┌─────────────────────────────────────────────────────┐
        │                  CORE BUSINESS LOGIC                │
        └─────────────────────────────────────────────────────┘
                    │
        ┌───────────┼───────────┬───────────┐
        │           │           │           │
        ▼           ▼           ▼           ▼
┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
│ANALYZERS│ │GENERATOR│ │INTEGRAT.│ │  UTILS  │
└─────────┘ └─────────┘ └─────────┘ └─────────┘
```

## 🔍 Detalle: Sistema de Análisis

```
┌──────────────────────────────────────────────────────────────┐
│              PROJECT ANALYZER SERVICE                        │
│  (Orquestador principal - Procesamiento paralelo)           │
└──────────────────────────────────────────────────────────────┘
                            │
                            ▼
                ┌───────────────────────┐
                │   ANALYZER FACTORY    │
                │   (Factory Pattern)   │
                └───────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   PYTHON     │    │     JAVA     │    │  JAVASCRIPT  │
│   ANALYZER   │    │   ANALYZER   │    │   ANALYZER   │
│   (AST)      │    │   (Regex)    │    │   (AST)      │
└──────────────┘    └──────────────┘    └──────────────┘
      │                   │                   │
      └───────────────────┴───────────────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │   CODE ANALYZER       │
              │   (Base Interface)    │
              │   • can_analyze()     │
              │   • analyze_file()    │
              │   • supported_langs   │
              └───────────────────────┘
```

## 📦 Flujo de Análisis de Proyecto

```
┌─────────┐
│  START  │
└────┬────┘
     │
     ▼
┌─────────────────────────┐
│ ProjectAnalyzerService  │
│ .analyze_project()      │
└────┬────────────────────┘
     │
     ▼
┌─────────────────────────┐
│ Collect Files           │
│ • Filter ignored        │
│ • Check size limits     │
│ • Verify analyzers      │
└────┬────────────────────┘
     │
     ▼
┌─────────────────────────┐
│ Parallel Processing?    │
└────┬────────────────────┘
     │
     ├─── YES ──┐
     │          ▼
     │    ┌──────────────────┐
     │    │ ThreadPoolExecutor│
     │    │ (4 workers)       │
     │    └──────────────────┘
     │          │
     └─── NO ───┤
                ▼
        ┌──────────────────┐
        │ For each file:   │
        │ 1. Get analyzer  │
        │ 2. Analyze file  │
        │ 3. Extract info  │
        └────┬─────────────┘
             │
             ▼
        ┌──────────────────┐
        │ Classify         │
        │ Components:      │
        │ • API            │
        │ • Database       │
        │ • Security       │
        │ • Integration    │
        │ • Utility        │
        └────┬─────────────┘
             │
             ▼
        ┌──────────────────┐
        │ Build Analysis   │
        │ • Total files    │
        │ • Total lines    │
        │ • Languages      │
        │ • Components     │
        └────┬─────────────┘
             │
             ▼
        ┌─────────┐
        │  DONE   │
        └─────────┘
```

## 🎯 Patrón Strategy: Analizadores

```
┌────────────────────────────────────────────────────┐
│              CodeAnalyzer (Interface)              │
│  ┌──────────────────────────────────────────────┐ │
│  │ + can_analyze(file_path) -> bool             │ │
│  │ + analyze_file(file_path) -> FileAnalysis    │ │
│  │ + supported_languages -> List[LanguageType]  │ │
│  └──────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────┘
                        △
                        │ implements
        ┌───────────────┼───────────────┐
        │               │               │
        ▼               ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│PythonAnalyzer│ │ JavaAnalyzer │ │  JSAnalyzer  │
├──────────────┤ ├──────────────┤ ├──────────────┤
│• Uses AST    │ │• Uses Regex  │ │• Uses AST    │
│• Extracts:   │ │• Extracts:   │ │• Extracts:   │
│  - Classes   │ │  - Classes   │ │  - Classes   │
│  - Functions │ │  - Methods   │ │  - Functions │
│  - Imports   │ │  - Imports   │ │  - Imports   │
│  - Endpoints │ │  - Endpoints │ │  - Endpoints │
│  - DB calls  │ │  - DB calls  │ │  - API calls │
└──────────────┘ └──────────────┘ └──────────────┘
```

## 🏭 Patrón Factory: Creación de Analizadores

```
┌─────────────────────────────────────────────────┐
│           AnalyzerFactory                       │
├─────────────────────────────────────────────────┤
│ - _analyzers: List[CodeAnalyzer]                │
├─────────────────────────────────────────────────┤
│ + get_analyzer(file_path) -> CodeAnalyzer?     │
│ + register_analyzer(analyzer) -> None           │
└─────────────────────────────────────────────────┘
                    │
                    │ manages
                    ▼
        ┌───────────────────────┐
        │   Registered          │
        │   Analyzers:          │
        │                       │
        │ [PythonAnalyzer]      │
        │ [JavaAnalyzer]        │
        │ [JSAnalyzer]          │
        │ [...]                 │
        └───────────────────────┘
```

## 🔧 Configuración: Pydantic Settings

```
┌─────────────────────────────────────────────────┐
│              Settings (Singleton)               │
├─────────────────────────────────────────────────┤
│ • service_name: str                             │
│ • version: str                                  │
│ • environment: str                              │
│ • debug: bool                                   │
├─────────────────────────────────────────────────┤
│ • openai: OpenAISettings                        │
│   ├─ api_key: str                               │
│   ├─ model: str                                 │
│   └─ max_tokens: int                            │
│                                                 │
│ • confluence: ConfluenceSettings                │
│   ├─ base_url: str                              │
│   ├─ email: str                                 │
│   └─ api_token: str                             │
│                                                 │
│ • jira: JiraSettings                            │
│ • eraser: EraserSettings                        │
│ • redis: RedisSettings                          │
│ • database: DatabaseSettings                    │
│ • analyzer: AnalyzerSettings                    │
└─────────────────────────────────────────────────┘
                    │
                    │ loads from
                    ▼
            ┌───────────────┐
            │   .env file   │
            └───────────────┘
```

## 📊 Modelos de Dominio

```
┌──────────────────────────────────────────────────┐
│              FileAnalysis                        │
├──────────────────────────────────────────────────┤
│ • file_path: str                                 │
│ • language: LanguageType                         │
│ • lines: int                                     │
│ • classes: List[str]                             │
│ • functions: List[str]                           │
│ • imports: List[str]                             │
│ • endpoints: List[Dict]                          │
│ • database_calls: List[str]                      │
│ • complexity: int                                │
└──────────────────────────────────────────────────┘
                    │
                    │ aggregates to
                    ▼
┌──────────────────────────────────────────────────┐
│            ProjectAnalysis                       │
├──────────────────────────────────────────────────┤
│ • repository_name: str                           │
│ • repository_owner: str                          │
│ • branch: str                                    │
│ • commit_hash: str?                              │
│ • files: List[FileAnalysis]                      │
│ • total_files: int                               │
│ • total_lines: int                               │
│ • languages: List[LanguageType]                  │
│ • components: Dict[ComponentType, List[str]]     │
│ • status: AnalysisStatus                         │
│ • created_at: datetime                           │
│ • completed_at: datetime?                        │
└──────────────────────────────────────────────────┘
```

## 🔄 Ciclo de Vida de un Análisis

```
┌─────────────┐
│   PENDING   │ ← Initial state
└──────┬──────┘
       │
       │ start_analysis()
       ▼
┌─────────────┐
│ PROCESSING  │ ← Analyzing files
└──────┬──────┘
       │
       ├─── Success ──┐
       │              ▼
       │         ┌─────────────┐
       │         │  COMPLETED  │ ← Analysis done
       │         └─────────────┘
       │
       └─── Error ────┐
                      ▼
                 ┌─────────────┐
                 │   FAILED    │ ← Error occurred
                 └─────────────┘
```

## 🎨 Clasificación de Componentes

```
┌──────────────────────────────────────────────────┐
│         Component Classification                 │
└──────────────────────────────────────────────────┘
                    │
        ┌───────────┼───────────┬───────────┬───────────┐
        │           │           │           │           │
        ▼           ▼           ▼           ▼           ▼
    ┌─────┐    ┌─────┐    ┌─────┐    ┌─────┐    ┌─────┐
    │ API │    │ DB  │    │ SEC │    │ INT │    │ UTL │
    └─────┘    └─────┘    └─────┘    └─────┘    └─────┘
       │          │          │          │          │
       │          │          │          │          │
    Has        Has        Has        Has        Default
  endpoints  db_calls   security   external   category
                        keywords    calls
```

## 📝 Logging Estructurado

```
┌─────────────────────────────────────────────────┐
│              Application Code                   │
└─────────────────────────────────────────────────┘
                    │
                    │ logger.info(...)
                    ▼
┌─────────────────────────────────────────────────┐
│              structlog                          │
│  ┌───────────────────────────────────────────┐ │
│  │ Processors:                               │ │
│  │ • merge_contextvars                       │ │
│  │ • add_log_level                           │ │
│  │ • add_logger_name                         │ │
│  │ • TimeStamper                             │ │
│  │ • add_app_context (service, version)      │ │
│  │ • format_exc_info                         │ │
│  │ • JSONRenderer / ConsoleRenderer          │ │
│  └───────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
                    │
        ┌───────────┴───────────┐
        │                       │
        ▼                       ▼
┌──────────────┐        ┌──────────────┐
│ Development  │        │  Production  │
│ (Colorized)  │        │    (JSON)    │
└──────────────┘        └──────────────┘
```

## 🧪 Testing Strategy

```
┌─────────────────────────────────────────────────┐
│                  pytest                         │
└─────────────────────────────────────────────────┘
                    │
        ┌───────────┼───────────┐
        │           │           │
        ▼           ▼           ▼
┌──────────┐ ┌──────────┐ ┌──────────┐
│  Unit    │ │Integration│ │   E2E    │
│  Tests   │ │  Tests    │ │  Tests   │
└──────────┘ └──────────┘ └──────────┘
     │
     ├─ test_python_analyzer.py
     ├─ test_factory.py
     ├─ test_project_analyzer.py
     └─ test_settings.py
```

---

## 🎯 Resumen de Arquitectura

### Capas
1. **Configuration Layer** - Pydantic Settings
2. **Domain Layer** - Models & Enums
3. **Business Logic Layer** - Analyzers, Generators, Integrations
4. **Infrastructure Layer** - Logging, Utils

### Patrones
- **Strategy** - Analizadores intercambiables
- **Factory** - Creación de analizadores
- **Singleton** - Configuración global

### Principios
- **SOLID** - Todos aplicados
- **Clean Code** - Código legible y mantenible
- **DRY** - Sin duplicación

---

**Versión:** 3.0.0  
**Estado:** ✅ Fase 1 Completada
