output "bucket_name" {
  description = "S3 bucket for private order receipts"
  value       = aws_s3_bucket.orders.bucket
}

output "rds_endpoint" {
  description = "RDS PostgreSQL endpoint (private)"
  value       = aws_db_instance.app.address
}

output "rds_identifier" {
  description = "RDS instance identifier"
  value       = aws_db_instance.app.identifier
}

output "rds_security_group_id" {
  description = "Security group attached to RDS"
  value       = aws_security_group.rds.id
}

output "app_security_group_id" {
  description = "Security group attached to the EC2 application host"
  value       = aws_security_group.app.id
}

output "ec2_instance_id" {
  description = "EC2 instance ID"
  value       = aws_instance.linux.id
}

output "ec2_public_ip" {
  description = "EC2 public IP address"
  value       = aws_instance.linux.public_ip
}

output "ec2_public_dns" {
  description = "EC2 public DNS"
  value       = aws_instance.linux.public_dns
}
