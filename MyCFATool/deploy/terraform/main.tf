terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.region
}

# VPC and Subnets (assuming they exist or create basic ones)
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
  tags = {
    Name = "mycfatool-vpc"
  }
}

resource "aws_subnet" "private_a" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = "${var.region}a"
  tags = {
    Name = "mycfatool-private-a"
  }
}

resource "aws_subnet" "private_b" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.2.0/24"
  availability_zone = "${var.region}b"
  tags = {
    Name = "mycfatool-private-b"
  }
}

# Security Group for RDS
resource "aws_security_group" "rds" {
  name_prefix = "mycfatool-rds-"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/16"]  # Only from VPC
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "mycfatool-rds-sg"
  }
}

# DB Subnet Group
resource "aws_db_subnet_group" "main" {
  name       = "mycfatool-db-subnet-group"
  subnet_ids = [aws_subnet.private_a.id, aws_subnet.private_b.id]

  tags = {
    Name = "mycfatool-db-subnet-group"
  }
}

# RDS PostgreSQL Instance
resource "aws_db_instance" "postgres" {
  identifier             = "mycfatool-prod"
  engine                 = "postgres"
  engine_version         = "15.4"
  instance_class         = "db.r6g.xlarge"
  allocated_storage      = 500
  max_allocated_storage  = 1000  # Auto-scaling
  storage_type           = "gp3"
  storage_encrypted      = true
  kms_key_id             = aws_kms_key.rds.arn

  db_name                = "mycfatool"
  username               = var.db_username
  password               = var.db_password
  port                   = 5432

  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name

  multi_az               = true
  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"

  auto_minor_version_upgrade = true
  deletion_protection    = true

  performance_insights_enabled = true
  monitoring_interval    = 60
  monitoring_role_arn    = aws_iam_role.rds_monitoring.arn

  enabled_cloudwatch_logs_exports = ["postgresql"]

  tags = {
    Name = "mycfatool-prod-db"
    Environment = "production"
  }
}

# KMS Key for RDS encryption
resource "aws_kms_key" "rds" {
  description             = "KMS key for MyCFATool RDS encryption"
  deletion_window_in_days = 30
  enable_key_rotation     = true
}

# IAM Role for RDS Enhanced Monitoring
resource "aws_iam_role" "rds_monitoring" {
  name = "mycfatool-rds-monitoring-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "monitoring.rds.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "rds_monitoring" {
  role       = aws_iam_role.rds_monitoring.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"
}

# ECR Repository
resource "aws_ecr_repository" "app" {
  name                 = "mycfatool-${var.environment}"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name        = "mycfatool-${var.environment}-ecr"
    Environment = var.environment
  }
}

# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "mycfatool-${var.environment}-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = {
    Name        = "mycfatool-${var.environment}-cluster"
    Environment = var.environment
  }
}

# Security Group for ALB
resource "aws_security_group" "alb" {
  name_prefix = "mycfatool-${var.environment}-alb-"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "mycfatool-${var.environment}-alb-sg"
    Environment = var.environment
  }
}

# Security Group for ECS Tasks
resource "aws_security_group" "ecs_tasks" {
  name_prefix = "mycfatool-${var.environment}-ecs-"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port       = 8050
    to_port         = 8050
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "mycfatool-${var.environment}-ecs-sg"
    Environment = var.environment
  }
}

# Application Load Balancer
resource "aws_lb" "main" {
  name               = "mycfatool-${var.environment}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = [aws_subnet.private_a.id, aws_subnet.private_b.id]

  enable_deletion_protection = var.environment == "production"

  tags = {
    Name        = "mycfatool-${var.environment}-alb"
    Environment = var.environment
  }
}

# Target Group
resource "aws_lb_target_group" "app" {
  name        = "mycfatool-${var.environment}-tg"
  port        = 8050
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"

  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 30
    matcher             = "200"
    path                = "/"
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = 5
    unhealthy_threshold = 2
  }

  tags = {
    Name        = "mycfatool-${var.environment}-tg"
    Environment = var.environment
  }
}

# ALB Listener
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.app.arn
  }
}

# IAM Role for ECS Task Execution
resource "aws_iam_role" "ecs_execution" {
  name = "mycfatool-${var.environment}-ecs-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_execution" {
  role       = aws_iam_role.ecs_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# IAM Role for ECS Task
resource "aws_iam_role" "ecs_task" {
  name = "mycfatool-${var.environment}-ecs-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
}

# Attach Secrets Manager policy to task role
resource "aws_iam_role_policy" "ecs_task_secrets" {
  name = "mycfatool-${var.environment}-ecs-task-secrets-policy"
  role = aws_iam_role.ecs_task.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = [
          aws_secretsmanager_secret.db_url.arn,
          aws_secretsmanager_secret.secret_key.arn,
          aws_secretsmanager_secret.fmp_api_key.arn
        ]
      }
    ]
  })
}

# Secrets Manager Secrets
resource "aws_secretsmanager_secret" "db_url" {
  name                    = "mycfatool/${var.environment}/db-url"
  description             = "Database connection URL for MyCFATool ${var.environment}"
  recovery_window_in_days = 30

  tags = {
    Environment = var.environment
  }
}

resource "aws_secretsmanager_secret" "secret_key" {
  name                    = "mycfatool/${var.environment}/secret-key"
  description             = "Secret key for MyCFATool ${var.environment}"
  recovery_window_in_days = 30

  tags = {
    Environment = var.environment
  }
}

resource "aws_secretsmanager_secret" "fmp_api_key" {
  name                    = "mycfatool/${var.environment}/fmp-api-key"
  description             = "FMP API key for MyCFATool ${var.environment}"
  recovery_window_in_days = 30

  tags = {
    Environment = var.environment
  }
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "ecs" {
  name              = "/ecs/mycfatool-${var.environment}-app"
  retention_in_days = 30

  tags = {
    Name        = "mycfatool-${var.environment}-logs"
    Environment = var.environment
  }
}

# Variables
variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment (staging or production)"
  type        = string
  default     = "staging"
}

variable "db_username" {
  description = "Database admin username"
  type        = string
  sensitive   = true
}

variable "db_password" {
  description = "Database admin password"
  type        = string
  sensitive   = true
}

variable "app_image" {
  description = "Docker image for the application"
  type        = string
  default     = ""
}

# Outputs
output "db_endpoint" {
  description = "RDS instance endpoint"
  value       = aws_db_instance.postgres.endpoint
}

output "db_port" {
  description = "RDS instance port"
  value       = aws_db_instance.postgres.port
}

output "db_name" {
  description = "Database name"
  value       = aws_db_instance.postgres.db_name
}

output "ecr_repository_url" {
  description = "ECR repository URL"
  value       = aws_ecr_repository.app.repository_url
}

output "ecs_cluster_name" {
  description = "ECS cluster name"
  value       = aws_ecs_cluster.main.name
}

output "alb_dns_name" {
  description = "ALB DNS name"
  value       = aws_lb.main.dns_name
}

output "secrets_arn_db_url" {
  description = "ARN of DB URL secret"
  value       = aws_secretsmanager_secret.db_url.arn
}

output "secrets_arn_secret_key" {
  description = "ARN of secret key secret"
  value       = aws_secretsmanager_secret.secret_key.arn
}

output "secrets_arn_fmp_api_key" {
  description = "ARN of FMP API key secret"
  value       = aws_secretsmanager_secret.fmp_api_key.arn
}

# ECS Task Definition
resource "aws_ecs_task_definition" "app" {
  family                   = "mycfatool-${var.environment}-app"
  task_role_arn            = aws_iam_role.ecs_task.arn
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "1024"
  memory                   = "2048"

  container_definitions = jsonencode([
    {
      name  = "mycfatool-app"
      image = var.app_image != "" ? var.app_image : "${aws_ecr_repository.app.repository_url}:latest"
      essential = true

      portMappings = [
        {
          containerPort = 8050
          protocol      = "tcp"
        }
      ]

      environment = [
        {
          name  = "FLASK_ENV"
          value = var.environment == "production" ? "production" : "development"
        },
        {
          name  = "REDIS_URL"
          value = "redis://mycfatool-redis:6379/0"  # Assuming Redis is added later or external
        }
      ]

      secrets = [
        {
          name      = "DATABASE_URL"
          valueFrom = aws_secretsmanager_secret.db_url.arn
        },
        {
          name      = "SECRET_KEY"
          valueFrom = aws_secretsmanager_secret.secret_key.arn
        },
        {
          name      = "FMP_API_KEY"
          valueFrom = aws_secretsmanager_secret.fmp_api_key.arn
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.ecs.name
          awslogs-region        = var.region
          awslogs-stream-prefix = "ecs"
        }
      }

      healthCheck = {
        command = [
          "CMD-SHELL",
          "curl -f http://localhost:8050/ || exit 1"
        ]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 60
      }
    }
  ])

  tags = {
    Name        = "mycfatool-${var.environment}-task-def"
    Environment = var.environment
  }
}

# ECS Service
resource "aws_ecs_service" "app" {
  name            = "mycfatool-${var.environment}-app-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.app.arn
  desired_count   = 2
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = [aws_subnet.private_a.id, aws_subnet.private_b.id]
    security_groups  = [aws_security_group.ecs_tasks.id]
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.app.arn
    container_name   = "mycfatool-app"
    container_port   = 8050
  }

  health_check_grace_period_seconds = 60

  deployment_configuration {
    maximum_percent        = 200
    minimum_healthy_percent = 50
    deployment_circuit_breaker {
      enable   = true
      rollback = true
    }
  }

  enable_ecs_managed_tags = true
  propagate_tags          = "SERVICE"

  tags = {
    Name        = "mycfatool-${var.environment}-service"
    Environment = var.environment
  }

  depends_on = [aws_lb_listener.http]
}