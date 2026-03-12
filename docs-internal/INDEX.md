# Internal Documentation Index

**⚠️ INTERNAL USE ONLY** — These documents contain operational details, cost information, and internal procedures.

---

## Core Internal Docs

### [TECHNICAL_SUMMARY.md](TECHNICAL_SUMMARY.md)

- Complete technical breakdown of all components
- Code flows and patterns
- Dependency analysis
- Reference for code reviews and onboarding

### [DEPLOYMENT_RUNBOOK.md](DEPLOYMENT_RUNBOOK.md)

- Step-by-step deployment procedures
- Environment setup and validation
- Deployment checklists
- Rollback procedures

### [OPERATIONS_RUNBOOK.md](OPERATIONS_RUNBOOK.md)

- Daily monitoring procedures
- Incident response playbook
- Performance tuning
- Troubleshooting procedures

### [COSTS_ANALYSIS.md](COSTS_ANALYSIS.md)

- Cost breakdown by service (Lambda, Bedrock, DynamoDB, S3)
- Monthly cost estimates
- Cost optimization strategies
- Pricing trends and forecasts

## Detailed Technical References

### [GUARDRAILS_DEEP_DIVE.md](GUARDRAILS_DEEP_DIVE.md)

- Safety mechanisms and their effectiveness
- Guardrail tuning and customization
- Failure mode analysis
- Future safety enhancements

### [TESTING_FRAMEWORK.md](TESTING_FRAMEWORK.md)

- Test infrastructure and architecture
- Fixture patterns and mocking strategies
- Adding new tests
- Debugging test failures
- Coverage analysis

### [INFRASTRUCTURE_DETAILS.md](INFRASTRUCTURE_DETAILS.md)

- Terraform module breakdown
- State management procedures
- AWS resource configuration
- Network and security setup

## Process & Procedural Docs

### [MAINTENANCE_SCHEDULE.md](MAINTENANCE_SCHEDULE.md)

- Regular maintenance tasks
- Database cleanup procedures
- Log retention policies
- Dependency updates

### [VERSION_HISTORY.md](VERSION_HISTORY.md)

- Internal version tracking
- Release notes and deployment logs
- Feature completion status
- Known issues per version

### [DECISION_LOG.md](DECISION_LOG.md)

- Architectural decisions made
- Trade-offs considered
- Rationale for key design choices
- Future decision frameworks

## Performance & Optimization

### [PERFORMANCE_BASELINE.md](PERFORMANCE_BASELINE.md)

- Latency benchmarks
- Throughput limits
- Resource utilization patterns
- Optimization opportunities

### [COST_OPTIMIZATION_GUIDE.md](COST_OPTIMIZATION_GUIDE.md)

- Detailed cost-saving tactics
- Service-by-service optimization
- Caching strategies analysis
- Budget forecasting

---

## Quick Index by Role

### 👨‍💻 Developer

1. **Onboarding**: [TECHNICAL_SUMMARY.md](TECHNICAL_SUMMARY.md)
2. **Local Setup**: See main [DEVELOPMENT.md](../docs/DEVELOPMENT.md)
3. **Adding Features**: [DECISION_LOG.md](DECISION_LOG.md), [TESTING_FRAMEWORK.md](TESTING_FRAMEWORK.md)
4. **Debugging**: [OPERATIONS_RUNBOOK.md](OPERATIONS_RUNBOOK.md), [INFRASTRUCTURE_DETAILS.md](INFRASTRUCTURE_DETAILS.md)

### 🚀 DevOps/SRE

1. **Initial Setup**: [DEPLOYMENT_RUNBOOK.md](DEPLOYMENT_RUNBOOK.md)
2. **Daily Operations**: [OPERATIONS_RUNBOOK.md](OPERATIONS_RUNBOOK.md)
3. **Incidents**: [OPERATIONS_RUNBOOK.md](OPERATIONS_RUNBOOK.md) → Incident section
4. **Infrastructure**: [INFRASTRUCTURE_DETAILS.md](INFRASTRUCTURE_DETAILS.md)
5. **Costs**: [COSTS_ANALYSIS.md](COSTS_ANALYSIS.md)

### 💰 Finance/Product

1. **Current Costs**: [COSTS_ANALYSIS.md](COSTS_ANALYSIS.md)
2. **Forecasts**: [COSTS_ANALYSIS.md](COSTS_ANALYSIS.md) → Projections
3. **Optimization**: [COST_OPTIMIZATION_GUIDE.md](COST_OPTIMIZATION_GUIDE.md)
4. **Features**: See main [ROADMAP.md](../docs/ROADMAP.md)

### 🔐 Security/Compliance

1. **Guardrails**: [GUARDRAILS_DEEP_DIVE.md](GUARDRAILS_DEEP_DIVE.md)
2. **Infrastructure Security**: [INFRASTRUCTURE_DETAILS.md](INFRASTRUCTURE_DETAILS.md)
3. **Incident Response**: [OPERATIONS_RUNBOOK.md](OPERATIONS_RUNBOOK.md)

---

## Document Status

| Document                   | Status     | Last Updated |
| -------------------------- | ---------- | ------------ |
| TECHNICAL_SUMMARY.md       | ✅ Current | March 2026   |
| DEPLOYMENT_RUNBOOK.md      | ✅ Current | March 2026   |
| OPERATIONS_RUNBOOK.md      | ✅ Current | March 2026   |
| COSTS_ANALYSIS.md          | ✅ Current | March 2026   |
| GUARDRAILS_DEEP_DIVE.md    | ✅ Current | March 2026   |
| TESTING_FRAMEWORK.md       | ✅ Current | March 2026   |
| INFRASTRUCTURE_DETAILS.md  | ✅ Current | March 2026   |
| MAINTENANCE_SCHEDULE.md    | ✅ Current | March 2026   |
| VERSION_HISTORY.md         | ✅ Current | March 2026   |
| DECISION_LOG.md            | ✅ Current | March 2026   |
| PERFORMANCE_BASELINE.md    | ✅ Current | March 2026   |
| COST_OPTIMIZATION_GUIDE.md | ✅ Current | March 2026   |

---

## Important Notes

- 🔒 These documents contain sensitive operational information
- 📋 Reference architectural decisions before making changes
- 🔄 Update [VERSION_HISTORY.md](VERSION_HISTORY.md) after every release
- 📊 Review [COSTS_ANALYSIS.md](COSTS_ANALYSIS.md) monthly
- ⚠️ Follow [OPERATIONS_RUNBOOK.md](OPERATIONS_RUNBOOK.md) for any production changes

---

**Classification**: Internal  
**Last Updated**: March 2026  
**Next Review**: June 2026  
**Access**: Alfred team only
