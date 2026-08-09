"""A curated reference list of known languages/frameworks/libraries/
platforms/tools -- the same four categories a CS resume's own "Technical
Skills" section groups things into.

core/matching.py's other heuristics are structural (a lead-in phrase, a
comma list, a capitalized run) and can find a real term in text no fixed
list would ever enumerate ahead of time ("cross-functional collaboration").
But no structural rule can tell "Docker" (a tool) from "Monte Carlo" (a
named mathematical technique) or "multi-body dynamics" (a physics
concept) -- both read as an ordinary capitalized proper noun or a plain
lowercase phrase. That distinction is fundamentally a lookup, not a text
shape, so this module exists specifically to answer it. It is deliberately
NOT exhaustive; add to it as real gaps turn up, the same way _STOPWORDS/
_CALENDAR_WORDS/_COMPOUND_FILLER in matching.py are grown over time.

Sourced against the 2025 Stack Overflow Developer Survey's technology
categories (survey.stackoverflow.co/2025/technology) rather than assembled
from memory, so coverage reflects what's actually in wide use, not just
what one person happened to think of.

Stored lowercase, keyed by how the term is actually written -- lookups in
matching.py compare against a candidate phrase's own lowercased text.
"""

LANGUAGES = {
    "javascript", "html", "css", "html/css", "html5", "css3", "sql",
    "python", "bash", "shell", "bash/shell", "shell scripting",
    "typescript", "java", "c#", "c++", "powershell", "c", "php", "go",
    "golang", "rust", "kotlin", "lua", "assembly", "ruby", "dart", "swift",
    "r", "groovy", "visual basic", "vba", "matlab", "perl", "gdscript",
    "elixir", "scala", "delphi", "lisp", "micropython", "zig", "erlang",
    "fortran", "ada", "f#", "ocaml", "gleam", "prolog", "cobol", "mojo",
    "haskell", "julia", "clojure", "objective-c", "nix", "solidity", "sas",
}

FRAMEWORKS_LIBRARIES = {
    "node.js", "nodejs", "react", "jquery", "next.js", "express",
    "express.js", "asp.net core", "angular", "angularjs", "vue.js", "vue",
    "fastapi", "spring boot", "spring", "flask", "asp.net", "wordpress",
    "django", "laravel", "svelte", "blazor", "nestjs", "ruby on rails",
    "rails", "astro", "deno", "symfony", "nuxt.js", "nuxt", "fastify",
    "axum", "phoenix", "drupal", "htmx", "solidjs", "flutter", "quarkus",
    "hugo", "leptos", "react native", "xamarin", "unity", "unreal engine",
    "gin", "fiber", "actix", "rocket", "electron", "redux", "zustand",
    "styled-components",
    "tailwind css", "tailwindcss", "bootstrap", "material-ui", "mui",
    "numpy", "pandas", "pytorch", "tensorflow", "tensorflow lite", "keras",
    "scikit-learn", "sklearn", "opencv", "matplotlib", "scipy", "seaborn",
    "plotly", "onnx", "onnx runtime", "coreml", "huggingface",
    "hugging face", "transformers", "xgboost", "lightgbm",
    "sqlalchemy", "hibernate", "prisma", "sequelize", "pydantic",
    "typeorm", "entity framework", "graphql", "apollo", "grpc", "protobuf",
    "polars", "langgraph", "langchain", "shadcn/ui", "shadcn",
    ".net", "rest api", "rest apis", "restful api", "restful apis",
    "material ui", "material-ui", "chakra ui", "eslint", "prettier",
    "sass", "scss", "sass/scss", "webassembly", "wasm", "three.js",
    "threejs", "android sdk", "openai api", "anthropic api",
    "pinecone", "weaviate", "faiss", "vector database", "vector databases",
    "openai", "anthropic",
}

SYSTEMS_PLATFORMS = {
    "docker", "amazon web services", "aws", "kubernetes", "k8s",
    "microsoft azure", "azure", "google cloud", "google cloud platform",
    "gcp", "cloudflare", "terraform", "podman", "digital ocean",
    "digitalocean", "vercel", "netlify", "heroku", "railway", "ibm cloud",
    "yandex cloud", "supabase", "firebase",
    "postgresql", "postgres", "mysql", "sqlite", "microsoft sql server",
    "sql server", "redis", "mongodb", "mariadb", "elasticsearch", "oracle",
    "dynamodb", "bigquery", "cloud firestore", "cosmos db", "snowflake",
    "influxdb", "databricks", "duckdb", "cassandra", "neo4j", "valkey",
    "clickhouse", "ibm db2", "amazon redshift", "cockroachdb", "couchdb",
    "opensearch", "couchbase", "surrealdb", "timescaledb",
    "linux", "ubuntu", "rhel", "red hat", "debian", "centos", "windows",
    "macos", "unix", "freebsd", "vmware",
    "arduino", "raspberry pi", "nvidia jetson", "fpga", "ros", "risc-v",
    "arm", "x86",
    # messaging/caching -- as core to a backend stack as a database
    "kafka", "rabbitmq", "celery", "memcached",
    # mobile-specific frameworks/runtimes
    "swiftui", "jetpack compose", "core data", "room", "dagger", "hilt",
    "serverless", "aws lambda", "azure functions", "hadoop",
    "apache hadoop",
}

# Protocols and network-layer terms -- as concretely nameable as a
# database or a language, just from a different layer of the stack.
NETWORKING = {
    "websockets", "tcp/ip", "http", "https", "http/https", "dns",
    "load balancing", "nginx", "apache http server",
}

# Security-specific standards/practices -- named things a candidate
# either knows or doesn't, same as a testing framework.
SECURITY = {
    "oauth", "oauth 2.0", "jwt", "sso", "tls", "ssl", "tls/ssl", "owasp",
    "penetration testing", "encryption", "zero trust", "iam",
}

# Named software-design concepts and patterns -- unlike a vague paradigm
# adjective ("scalable", "real-time") paired with a generic noun, each of
# these is a specific, well-defined term with its own established name
# that a CS curriculum and a resume's own "Concepts" section both use.
ARCHITECTURE_CONCEPTS = {
    "microservices", "monolith", "event-driven architecture", "oop",
    "object-oriented programming", "system design", "api design", "mvc",
    "design patterns", "data structures", "algorithms",
    "data structures & algorithms", "data structures and algorithms",
    "distributed systems", "concurrency", "multithreading",
    "multi-threading", "blockchain", "smart contracts", "web3",
}

TOOLS_TESTING = {
    "git", "github", "gitlab", "bitbucket", "npm", "pip", "yarn", "pnpm",
    "cargo", "gradle", "maven", "make", "cmake", "webpack", "vite",
    "babel", "bazel", "poetry", "homebrew", "nuget", "apt", "chocolatey",
    "composer", "msbuild", "pacman", "bun", "ninja",
    "github actions", "jenkins", "circleci", "travis ci", "gitlab ci",
    "ci/cd", "ansible", "puppet", "chef", "vagrant", "prometheus",
    "datadog", "splunk", "new relic",
    # observability/SRE/deployment -- Prometheus's universal pairing
    # partner and the rest of that same toolbox
    "grafana", "opentelemetry", "pagerduty", "argocd", "helm", "istio",
    "linkerd", "pulumi",
    # data/ML pipeline and orchestration tools
    "airflow", "spark", "mlflow", "dask", "ray", "tableau", "looker",
    "sagemaker", "vertex ai",
    "pytest", "unittest", "googletest", "gtest", "junit", "mocha", "jest",
    "cypress", "selenium", "behave", "cucumber", "playwright",
    "xctest", "espresso", "fastlane", "bitrise",
    "postman", "swagger", "openapi", "jira", "confluence", "figma",
    "slack", "notion", "trello", "asana", "linear", "storybook",
    "visual studio code", "vs code", "visual studio", "intellij idea",
    "intellij", "vim", "neovim", "pycharm", "android studio", "jupyter",
    "jupyter notebook", "sublime text", "xcode", "webstorm", "eclipse",
    "phpstorm", "emacs", "clion", "goland", "rubymine", "rstudio",
    "unit testing", "integration testing", "unit & integration testing",
    "unit/integration testing", "continuous integration", "load testing",
    "continuous deployment", "continuous delivery", "logging",
    "application performance monitoring", "apm",
    "test-driven development", "tdd", "agile", "scrum", "kanban",
}

# Named fields/technology areas, not a specific product -- "machine
# learning" isn't a tool the way "PyTorch" is, but it's exactly as
# concrete and nameable as one, and just as standard a resume category.
FIELDS = {
    "machine learning", "deep learning", "artificial intelligence",
    "natural language processing", "nlp", "computer vision",
    "large language model", "large language models", "llm", "llms",
    "generative ai", "neural network", "neural networks",
    "reinforcement learning", "data science", "data engineering",
    "cloud computing", "devops", "site reliability engineering", "sre",
    "retrieval-augmented generation", "rag", "prompt engineering",
    "mlops", "model fine-tuning", "fine-tuning", "embeddings",
    "dbt", "etl", "elt", "etl/elt", "data warehousing", "data pipelines",
    "a/b testing", "feature flags",
}

ALL_TECH_NAMES = (
    LANGUAGES
    | FRAMEWORKS_LIBRARIES
    | SYSTEMS_PLATFORMS
    | TOOLS_TESTING
    | FIELDS
    | NETWORKING
    | SECURITY
    | ARCHITECTURE_CONCEPTS
)
