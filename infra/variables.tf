variable "aws_region" {
  type    = string
  default = "us-west-2"
}

variable "bucket_name" {
  type        = string
  description = "Globally unique S3 bucket name (pattern: dangoko-avance2-<account>-<region>-<suffix>)"
}

variable "vpc_id" {
  type        = string
  description = "VPC where the application and RDS run"
}

variable "db_subnet_ids" {
  type        = list(string)
  description = "Two subnet IDs in different AZs for the RDS subnet group"
}

variable "allowed_cidr" {
  type        = string
  description = "CIDR allowed to SSH and reach port 5000 (e.g. your public IP /32)"
  default     = "0.0.0.0/0"
}

variable "ec2_ami" {
  type        = string
  description = "AMI ID for the Linux host (Amazon Linux 2023)"
}

variable "ec2_instance_type" {
  type    = string
  default = "t3.micro"
}

variable "ec2_subnet_id" {
  type        = string
  description = "Subnet where the EC2 instance will be launched"
}

variable "ec2_key_name" {
  type        = string
  description = "EC2 key pair name for SSH access (leave empty to skip)"
  default     = ""
}

variable "ec2_instance_profile" {
  type        = string
  description = "IAM instance profile name for S3 access (leave empty to skip)"
  default     = ""
}

variable "db_identifier" {
  type    = string
  default = "dangoko-avance2-rds"
}

variable "db_instance_class" {
  type    = string
  default = "db.t3.micro"
}

variable "db_name" {
  type    = string
  default = "dangoko"
}

variable "db_username" {
  type      = string
  sensitive = true
}

variable "db_password" {
  type      = string
  sensitive = true
}
