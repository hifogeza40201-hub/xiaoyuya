const { execSync } = require('child_process');
const path = require('path');

const workspace = 'C:/Users/Admin/.openclaw/workspace';

process.chdir(workspace);

// Set environment variables for credentials
process.env.HOME = 'C:/Users/Admin';

try {
    console.log('Attempting to push...');
    const result = execSync('git push origin master', {
        encoding: 'utf8',
        timeout: 30000,
        stdio: ['pipe', 'pipe', 'pipe']
    });
    console.log('Success:', result);
} catch (error) {
    console.log('Error:', error.message);
    console.log('Stdout:', error.stdout);
    console.log('Stderr:', error.stderr);
}
