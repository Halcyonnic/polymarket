# AI Agent Requirements for Python Development

## Code Quality Standards

### 1. Code Style

- Follow PEP 8 style guidelines
- Use type hints for function parameters and return values
- Maintain consistent naming conventions (snake_case for functions/variables, PascalCase for classes)
- Keep functions focused and under 50 lines when possible
- Use meaningful variable and function names

### 2. Documentation

- Include docstrings for all public modules, classes, and functions
- Use Google or NumPy docstring format consistently
- Document complex algorithms with inline comments
- Maintain an up-to-date README.md with setup instructions
- Document API endpoints and data models clearly

### 3. Type Safety

- Use type hints throughout the codebase
- Make sure there is no ruff or mypy errors
- Avoid using `Any` type unless absolutely necessary
- Use TypedDict or dataclasses for structured data

## Error Handling

### 4. Exception Management

- Use specific exception types rather than bare `except`
- Provide meaningful error messages
- Log errors appropriately with context
- Handle edge cases and validate inputs
- Use custom exceptions for domain-specific errors

### 5. Validation

- Validate all external inputs (API requests, file uploads, user input)
- Use pydantic or similar libraries for data validation
- Sanitize data before processing
- Check for None values and empty collections

## Testing Requirements

### 6. Test Coverage

- Maintain minimum 80% code coverage
- Write unit tests for all business logic
- Include integration tests for API endpoints
- Test edge cases and error conditions
- Use pytest as the testing framework

### 7. Test Quality

- Follow Arrange-Act-Assert pattern
- Use fixtures for common test setup
- Mock external dependencies
- Keep tests independent and isolated
- Use descriptive test names

## Dependencies & Environment

### 8. Package Management

- Use `pyproject.toml` for dependency management
- Pin major versions, allow minor/patch updates
- Separate development and production dependencies
- Document system-level dependencies
- Keep dependencies minimal and up-to-date

### 9. Virtual Environments

- Always use virtual environments (venv, conda, poetry)
- Document Python version requirements (minimum 3.8+)
- Include requirements.txt or pyproject.toml
- Use `.env` files for environment-specific configuration

## Security

### 10. Security Best Practices

- Never commit secrets, API keys, or passwords
- Use environment variables for sensitive configuration
- Validate and sanitize all user inputs
- Keep dependencies updated for security patches
- Use HTTPS for all external API calls
- Implement proper authentication and authorization

### 11. Data Protection

- Hash passwords using bcrypt or argon2
- Encrypt sensitive data at rest
- Use secure random generators for tokens
- Implement rate limiting for APIs
- Follow OWASP security guidelines

## Performance

### 12. Optimization

- Use async/await for I/O-bound operations
- Implement caching where appropriate
- Avoid N+1 queries in database operations
- Use generators for large datasets
- Profile code to identify bottlenecks

### 13. Resource Management

- Close file handles and database connections properly
- Use context managers (`with` statements)
- Implement connection pooling for databases
- Set appropriate timeouts for network requests
- Monitor memory usage for large data operations

## Architecture

### 14. Code Organization

- Follow separation of concerns principles
- Use layered architecture (presentation, business, data)
- Keep business logic separate from framework code
- Use dependency injection
- Implement SOLID principles

### 15. API Design

- Follow RESTful conventions for HTTP APIs
- Use consistent response formats
- Implement proper HTTP status codes
- Version APIs appropriately
- Document endpoints with OpenAPI/Swagger

## Version Control

### 16. Git Practices

- Write clear, descriptive commit messages
- Use feature branches for development
- Keep commits atomic and focused
- Review code before merging
- Tag releases appropriately

### 17. Code Review

- Review all code changes before merging
- Check for code quality, security, and performance
- Ensure tests pass and coverage is maintained
- Verify documentation is updated
- Validate type hints and linting pass

## Logging & Monitoring

### 18. Logging

- Use Python's `logging` module
- Log at appropriate levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Include contextual information in logs
- Avoid logging sensitive information
- Use structured logging (JSON) for production

### 19. Monitoring

- Implement health check endpoints
- Track key metrics (response time, error rate)
- Use APM tools in production
- Set up alerts for critical failures
- Monitor resource usage

## Documentation

### 20. Project Documentation

- Maintain comprehensive README.md
- Document architecture decisions
- Include setup and deployment instructions
- Provide examples and usage guides
- Keep documentation in sync with code
