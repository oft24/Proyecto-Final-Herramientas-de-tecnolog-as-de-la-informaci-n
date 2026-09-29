terraform {
  required_version = ">= 1.8.0, < 2.0.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.70"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# ─────────────────────────────────────────────
# Security Group – application (EC2)
# ─────────────────────────────────────────────
resource "aws_security_group" "app" {
  name        = "dangoko-avance2-app-sg"
  description = "Application host: SSH and port 5000 from authorised CIDRs only"
  vpc_id      = var.vpc_id

  ingress {
    description = "SSH from authorised CIDR"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.allowed_cidr]
  }

  ingress {
    description = "Flask API from authorised CIDR"
    from_port   = 5000
    to_port     = 5000
    protocol    = "tcp"
    cidr_blocks = [var.allowed_cidr]
  }

  egress {
    description = "Allow all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "dangoko-avance2-app-sg"
    Project     = "dangoko-avance2"
    Environment = "qa"
  }
}

# ─────────────────────────────────────────────
# Security Group – RDS
# ─────────────────────────────────────────────
resource "aws_security_group" "rds" {
  name        = "dangoko-avance2-rds-sg"
  description = "Only the application security group may reach PostgreSQL"
  vpc_id      = var.vpc_id

  ingress {
    description     = "PostgreSQL from the application SG only"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.app.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "dangoko-avance2-rds-sg"
    Project     = "dangoko-avance2"
    Environment = "qa"
  }
}

# ─────────────────────────────────────────────
# EC2 – Linux host
# ─────────────────────────────────────────────
resource "aws_instance" "linux" {
  ami                         = var.ec2_ami
  instance_type               = var.ec2_instance_type
  subnet_id                   = var.ec2_subnet_id
  vpc_security_group_ids      = [aws_security_group.app.id]
  associate_public_ip_address = true
  iam_instance_profile        = var.ec2_instance_profile != "" ? var.ec2_instance_profile : null
  key_name                    = var.ec2_key_name != "" ? var.ec2_key_name : null

  user_data = base64encode(<<-EOF
    #!/bin/bash
    set -e
    dnf update -y
    dnf install -y git python3 python3-pip postgresql15 unzip
    # Docker
    dnf install -y docker
    systemctl enable docker
    systemctl start docker
    usermod -aG docker ec2-user
    # Docker Compose plugin
    mkdir -p /usr/local/lib/docker/cli-plugins
    curl -SL https://github.com/docker/compose/releases/download/v2.29.1/docker-compose-linux-x86_64 \
      -o /usr/local/lib/docker/cli-plugins/docker-compose
    chmod +x /usr/local/lib/docker/cli-plugins/docker-compose
    # AWS CLI v2
    curl -s "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o /tmp/awscliv2.zip
    unzip -q /tmp/awscliv2.zip -d /tmp
    /tmp/aws/install
    # Terraform
    TERRAFORM_VERSION="1.9.5"
    curl -s "https://releases.hashicorp.com/terraform/$${TERRAFORM_VERSION}/terraform_$${TERRAFORM_VERSION}_linux_amd64.zip" \
      -o /tmp/terraform.zip
    unzip -q /tmp/terraform.zip -d /usr/local/bin
    chmod +x /usr/local/bin/terraform
    # Signal done
    touch /tmp/user-data-done
  EOF
  )

  tags = {
    Name        = "dangoko-avance2-linux"
    Project     = "dangoko-avance2"
    Environment = "qa"
    Purpose     = "docker-host"
  }

  lifecycle {
    ignore_changes = [user_data]
  }
}

# ─────────────────────────────────────────────
# S3 – private order receipts
# ─────────────────────────────────────────────
resource "aws_s3_bucket" "orders" {
  bucket        = var.bucket_name
  force_destroy = false

  tags = {
    Name        = var.bucket_name
    Project     = "dangoko-avance2"
    Environment = "qa"
    Purpose     = "private-order-receipts"
  }

  lifecycle {
    ignore_changes = [object_lock_enabled]
  }
}

resource "aws_s3_bucket_public_access_block" "orders" {
  bucket                  = aws_s3_bucket.orders.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "orders" {
  bucket = aws_s3_bucket.orders.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_versioning" "orders" {
  bucket = aws_s3_bucket.orders.id
  versioning_configuration {
    status = "Enabled"
  }
}

# ─────────────────────────────────────────────
# RDS – PostgreSQL
# ─────────────────────────────────────────────
resource "aws_db_subnet_group" "app" {
  name       = "dangoko-avance2-db-subnets"
  subnet_ids = var.db_subnet_ids

  tags = {
    Project     = "dangoko-avance2"
    Environment = "qa"
  }
}

resource "aws_db_instance" "app" {
  identifier              = var.db_identifier
  engine                  = "postgres"
  engine_version          = "16.15"
  instance_class          = var.db_instance_class
  allocated_storage       = 20
  max_allocated_storage   = 50
  storage_type            = "gp3"
  storage_encrypted       = true
  db_name                 = var.db_name
  username                = var.db_username
  password                = var.db_password
  port                    = 5432
  publicly_accessible     = false
  multi_az                = false
  skip_final_snapshot     = true
  deletion_protection     = false
  db_subnet_group_name    = aws_db_subnet_group.app.name
  vpc_security_group_ids  = [aws_security_group.rds.id]
  backup_retention_period = 1
  apply_immediately       = true

  tags = {
    Project     = "dangoko-avance2"
    Environment = "qa"
    Purpose     = "marketplace-database"
  }
}
