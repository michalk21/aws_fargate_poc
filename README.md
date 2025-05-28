# AWS ECS + RDS Infrastructure with Terraform

## Project Overview

This Terraform configuration creates a complete AWS infrastructure for running a containerized application with the following components:

- **ECS Fargate Service** - Running Docker containers with REST API on port 8080
- **Application Load Balancer** - HTTPS endpoint with IP-based access control
- **RDS PostgreSQL** - Database accessible from the application
- **VPC Networking** - Secure network architecture with public/private subnets

## Architecture

```
Internet (${var.app_access_ips})
           ↓ HTTPS (443)
    [Application Load Balancer]
           ↓ HTTP (8080)
      [ECS Fargate Tasks]
           ↓ PostgreSQL (5432)
        [RDS Database]
```

## Prerequisites

- AWS CLI configured with appropriate credentials
- Terraform >= 1.0
- Docker image available in a registry (ECR or Docker Hub)

## Quick Start

### 1. Clone and Configure

```bash
git clone https://github.com/michalk21/aws_fargate_poc.git
cd aws_fargate_poc
```

### 2. Set Required Variables

Create `terraform.tfvars` file:

```hcl
# Required variables
app_docker_image = "michalk21/sample_rest_app:1.0.0" # Replace with your Docker image. You can use it as sample. Source code of it in subdir ./deploy_sample_app/sample_rest_app/
app_access_ips = ["W.X.Y.Z/24", "AA.WWW.XX.YY/32"] # Whitelist of ip addresses which will have access to endpoint
db_password  = "YourSecurePassword123!" # Use a strong password
aws_region   = "us-central-1"              # Choose your preferred region

domain_name = "aws.flowoo.pl" # Domain address to use it as endpoint to access service
aws_route53_zone_id = "Z0711042IZRC7J5ODQK7" # AWS Route53 Zone ID where dns record will be created to use it to access service and generate certificate
```

### 3. Deploy Infrastructure

```bash
# Initialize Terraform
terraform init

# Preview changes
terraform plan

# Apply configuration
terraform apply
```

### 4. Get Connection Details

```bash
# Get Load Balancer DNS name
terraform output load_balancer_dns

```

## Configuration

### Environment Variables in Container

The following environment variables are automatically set in your container:

- `DB_HOST` - RDS address
- `DB_POST` - RDS port
- `DB_NAME` - Database name
- `DB_USER` - Database username
- `DB_PASSWORD` - Database password

## Current Limitations and areas to improve

⚠️ **This is a minimal viable implementation. For production use, consider:**

- Store Terraform state remotly in S3 with DynamoDB locking
- Use modules if feasible, for example use terraform-aws-modules/vpc/aws instead of inline vpc config, (sg, rds, etc)
- Add better tagging for resource, for example project, organization, env, maybe use module to that
- Implement proper secrets management (AWS Secrets Manager) for RDS db password (password rotation)
- Add WAF to Application Load Balancer if neccessary
- Add auto-scaling policies to ECS
- Enable Multi-AZ for RDS
- Add comprehensive monitoring and alerting
- Implement backup and disaster recovery

## Outputs

After successful deployment, you'll get:

```bash
load_balancer_dns = "xxxxx.yyyy.elb.amazonaws.com"
```

## Accessing Your Application

1. **Get the ALB DNS name** from Terraform outputs
2. **Add DNS record** pointing to the ALB (or use DNS name directly for testing)
3. **Access via HTTPS** from whitelisted IP range: `https://${var.load_balancer_dns}` or `https://${domain_name}`

## Cleanup

To destroy all created resources:

```bash
terraform destroy
```

⚠️ **Warning:** This will permanently delete all data including the database.

## Cost Estimation

Approximate monthly costs : TODO

## Support

For issues or questions:

1. Review AWS CloudWatch logs
2. Verify your `terraform.tfvars` configuration
3. Ensure your Docker image is accessible and properly configured

## License

This project is licensed under the MIT License - see the LICENSE file for details.
