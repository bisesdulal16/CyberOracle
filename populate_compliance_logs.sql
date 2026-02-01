INSERT INTO logs (created_at, endpoint, method, status_code, message, masked)
VALUES
(NOW(), '/api/patient/1', 'POST', 200, 'Processed request successfully', false),
(NOW(), '/api/patient/2', 'POST', 200, 'Processed request successfully', false),
(NOW(), '/api/login', 'POST', 401, 'Unauthorized access attempt', false),
(NOW(), '/api/login', 'POST', 403, 'Forbidden access attempt', false),
(NOW(), '/api/patient', 'POST', 200, 'SSN=***MASKED***', true);