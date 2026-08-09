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
    "vhdl", "verilog",
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
    "material ui", "chakra ui", "eslint", "prettier",
    "sass", "scss", "sass/scss", "webassembly", "wasm", "three.js",
    "threejs", "android sdk", "openai api", "anthropic api",
    "pinecone", "weaviate", "faiss", "vector database", "vector databases",
    "openai", "anthropic",
    # ML deployment/serving/training extras
    "tensorflow serving", "torchserve", "kubeflow", "cuda",
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
    # specific cloud-provider services -- named as concretely as any
    # other platform above, just under a specific provider's umbrella
    "ec2", "s3", "rds", "vpc", "cloudformation", "cloudwatch", "ecs",
    "eks", "api gateway", "route 53",
    "azure devops", "azure active directory", "azure ad",
    "azure kubernetes service", "aks", "azure blob storage",
    "cloud functions", "cloud run", "compute engine", "pub/sub",
    "docker compose", "perforce", "svn",
    # enterprise platforms -- as real and nameable as any dev tool, just
    # from the business-software side of a stack
    "salesforce", "sap", "servicenow",
    "embedded systems", "rtos", "iot",
    # systems administration / infra
    "active directory", "virtualization", "hyper-v", "vsphere",
    "storage area network", "san", "network attached storage", "nas",
    "raid", "high availability", "disaster recovery", "vpn", "dhcp",
    "itil", "saltstack", "elk stack", "logstash", "kibana", "nagios",
    # security tooling
    "nessus", "wireshark", "metasploit", "burp suite", "kali linux",
    "nmap", "okta", "semgrep", "checkmarx", "qualys", "guardduty",
    "sentinelone", "azure sentinel", "trivy", "aqua security", "kms",
    "aws kms", "vault", "hashicorp vault",
    # more DevOps/SRE and sysadmin tools
    "containerd", "flux", "veeam", "veritas", "crowdstrike", "intune",
    "solarwinds",
    # QA/SDET test-case management
    "testrail", "zephyr",
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
    "soc 2", "gdpr", "hipaa", "pci dss", "siem", "soc",
    "threat intelligence", "vulnerability assessment", "digital forensics",
    "malware analysis", "endpoint detection and response", "edr",
    "intrusion detection system", "ids", "intrusion prevention system",
    "ips", "cryptography", "public key infrastructure", "pki",
    "network security", "application security", "devsecops", "sast",
    "dast", "threat modeling", "red team", "blue team", "purple team",
    "cissp", "ceh", "firewalls", "firewall",
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
    "solid principles", "clean code", "domain-driven design", "ddd",
    "cap theorem", "infrastructure as code", "iac",
    "configuration management", "blue-green deployment",
    "canary deployment", "immutable infrastructure", "incident response",
    "on-call", "runbooks", "routing & switching", "chaos engineering",
}

# Industry certifications -- a specific, named, verifiable credential is
# exactly as concrete a resume keyword as a tool or a language.
CERTIFICATIONS = {
    "aws certified solutions architect", "pmp",
    "certified kubernetes administrator", "cka", "comptia security+",
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
    "sagemaker", "vertex ai", "power bi", "teamcity",
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
    # QA/SDET
    "quality assurance", "qa", "manual testing", "automated testing",
    "appium", "testng", "robot framework",
    "behavior-driven development", "bdd", "gherkin", "test case design",
    "test plans", "regression testing", "smoke testing",
    "black box testing", "white box testing", "exploratory testing",
    "defect tracking", "test coverage", "boundary value analysis",
    # performance/load testing
    "jmeter", "loadrunner", "gatling", "k6", "stress testing",
    "performance benchmarking",
    # integration/contract/API testing
    "contract testing", "pact", "service virtualization", "mock servers",
    "end-to-end testing", "e2e testing", "api testing", "restassured",
    "test environment management", "sandbox testing", "soapui",
    "graphql testing",
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
    # data engineering extras
    "apache beam", "presto", "trino", "apache nifi", "apache flink",
    "delta lake", "apache iceberg", "parquet", "avro", "data lake",
    "data mesh", "data modeling", "star schema", "luigi",
    "great expectations", "data quality", "data governance",
    "data catalog", "apache hive", "hdfs", "sqoop",
    "change data capture", "cdc", "batch processing", "stream processing",
    "real-time processing",
    # ML engineering extras
    "feature engineering", "model deployment", "model serving",
    "model monitoring", "hyperparameter tuning", "gpu computing",
    "distributed training", "data labeling", "feature store",
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
    | CERTIFICATIONS
)
