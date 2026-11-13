# Bitácora de despliegue – MiRitmo (Entregable 1)

Cada comando con su salida. Los secretos se omiten o aparecen como `***`.

## 1. Identidad de la sesión AWS

_2026-11-13 11:50_ · código de salida 0

```
> aws sts get-caller-identity --profile miritmo
{
    "UserId": "AROAULMOKKJQ4NMMXZO2L:94d80438-5021-70c9-8465-db1f91703d30",
    "Account": "299335570017",
    "Arn": "arn:aws:sts::299335570017:assumed-role/AccountFullAccessRole/94d80438-5021-70c9-8465-db1f91703d30"
}
```

## 2. Plan de la cuenta (Free Tier)

_2026-11-13 11:50_ · código de salida 0

```
> aws freetier get-account-plan-state --profile miritmo --region us-east-1
{
    "accountId": "299335570017",
    "accountPlanType": "FREE",
    "accountPlanStatus": "ACTIVE",
    "accountPlanRemainingCredits": {
        "amount": 100.0,
        "unit": "USD"
    },
    "accountPlanExpirationDate": "2027-05-13T14:33:30.809000+00:00"
}
```

## 3. Rol de la sesión

_2026-11-13 11:50_ · código de salida 0

```
> aws iam list-roles --profile miritmo --query Roles[?RoleName=='AccountFullAccessRole'].[RoleName,Path,Arn] --output text
AccountFullAccessRole	/managed/	arn:aws:iam::299335570017:role/managed/AccountFullAccessRole
```

## 4. Bloqueo de acceso público de S3 a nivel cuenta

_2026-11-13 11:50_ · código de salida 254

```
> aws s3control get-public-access-block --account-id 299335570017 --profile miritmo --region us-east-2
[stderr]

aws: [ERROR]: An error occurred (NoSuchPublicAccessBlockConfiguration) when calling the GetPublicAccessBlock operation: The public access block configuration was not found
```

## 5. Límites de Lambda en la cuenta

_2026-11-13 11:50_ · código de salida 0

```
> aws lambda get-account-settings --profile miritmo --region us-east-2 --query AccountLimit
{
    "TotalCodeSize": 322122547200,
    "CodeSizeUnzipped": 262144000,
    "CodeSizeZipped": 52428800,
    "ConcurrentExecutions": 400,
    "UnreservedConcurrentExecutions": 400
}
```

## 6. Simulador de políticas IAM: acciones del despliegue (sin crear recursos)

_2026-11-13 11:50_ · código de salida 0

```
> aws iam simulate-principal-policy --profile miritmo --policy-source-arn arn:aws:iam::299335570017:role/managed/AccountFullAccessRole --action-names s3:CreateBucket s3:PutBucketPublicAccessBlock s3:PutBucketPolicy s3:PutObject cloudfront:CreateOriginAccessControl cloudfront:CreateDistribution cloudfront:CreateInvalidation iam:CreateRole iam:AttachRolePolicy iam:PassRole lambda:CreateFunction lambda:CreateFunctionUrlConfig lambda:AddPermission lambda:UpdateFunctionConfiguration logs:FilterLogEvents --query EvaluationResults[].[EvalActionName,EvalDecision] --output text
s3:CreateBucket	explicitDeny
s3:PutBucketPublicAccessBlock	explicitDeny
s3:PutBucketPolicy	explicitDeny
s3:PutObject	explicitDeny
cloudfront:CreateOriginAccessControl	allowed
cloudfront:CreateDistribution	allowed
cloudfront:CreateInvalidation	allowed
iam:CreateRole	allowed
iam:AttachRolePolicy	allowed
iam:PassRole	allowed
lambda:CreateFunction	explicitDeny
lambda:CreateFunctionUrlConfig	explicitDeny
lambda:AddPermission	explicitDeny
lambda:UpdateFunctionConfiguration	explicitDeny
logs:FilterLogEvents	allowed
```

## 7. Simulador IAM con aws:RequestedRegion=us-east-2

_2026-11-13 11:50_ · código de salida 0

```
> aws iam simulate-principal-policy --profile miritmo --policy-source-arn arn:aws:iam::299335570017:role/managed/AccountFullAccessRole --action-names s3:CreateBucket s3:PutBucketPublicAccessBlock s3:PutBucketPolicy s3:PutObject lambda:CreateFunction lambda:CreateFunctionUrlConfig lambda:AddPermission lambda:UpdateFunctionConfiguration --context-entries ContextKeyName=aws:RequestedRegion,ContextKeyValues=us-east-2,ContextKeyType=string --query EvaluationResults[].[EvalActionName,EvalDecision,join(',',MatchedStatements[].SourcePolicyId)] --output text
s3:CreateBucket	allowed	AdministratorAccess
s3:PutBucketPublicAccessBlock	allowed	AdministratorAccess
s3:PutBucketPolicy	allowed	AdministratorAccess
s3:PutObject	allowed	AdministratorAccess
lambda:CreateFunction	allowed	AdministratorAccess
lambda:CreateFunctionUrlConfig	allowed	AdministratorAccess
lambda:AddPermission	allowed	AdministratorAccess
lambda:UpdateFunctionConfiguration	allowed	AdministratorAccess
```
