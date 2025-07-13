#!/usr/bin/env node

/**
 * Mock模式切换工具
 * 用于快速切换Mock模式和真实API模式
 */

const fs = require('fs');
const path = require('path');

const ENV_FILE = path.join(__dirname, '../.env.local');

function readEnvFile() {
  if (!fs.existsSync(ENV_FILE)) {
    return {};
  }
  
  const content = fs.readFileSync(ENV_FILE, 'utf8');
  const env = {};
  
  content.split('\n').forEach(line => {
    const trimmed = line.trim();
    if (trimmed && !trimmed.startsWith('#')) {
      const [key, ...valueParts] = trimmed.split('=');
      if (key && valueParts.length > 0) {
        env[key.trim()] = valueParts.join('=').trim();
      }
    }
  });
  
  return env;
}

function writeEnvFile(env) {
  const lines = [
    '# Mock开关配置',
    '# true: 使用mock数据，false: 使用真实API',
    `NEXT_PUBLIC_USE_MOCK=${env.NEXT_PUBLIC_USE_MOCK || 'true'}`,
    '',
    '# API基础URL',
    `NEXT_PUBLIC_API_BASE_URL=${env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api'}`,
    '',
    '# 开发环境配置',
    `NODE_ENV=${env.NODE_ENV || 'development'}`
  ];
  
  fs.writeFileSync(ENV_FILE, lines.join('\n') + '\n');
}

function getCurrentMode() {
  const env = readEnvFile();
  return env.NEXT_PUBLIC_USE_MOCK !== 'false';
}

function toggleMock() {
  const env = readEnvFile();
  const currentMode = env.NEXT_PUBLIC_USE_MOCK !== 'false';
  
  env.NEXT_PUBLIC_USE_MOCK = currentMode ? 'false' : 'true';
  writeEnvFile(env);
  
  const newMode = !currentMode;
  console.log(`✅ Mock模式已${newMode ? '启用' : '禁用'}`);
  console.log(`📊 当前模式: ${newMode ? 'Mock数据' : '真实API'}`);
  
  if (!newMode) {
    console.log(`🔗 API地址: ${env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api'}`);
  }
  
  console.log('\n💡 请重启开发服务器以应用更改');
}

function setMockMode(enabled) {
  const env = readEnvFile();
  env.NEXT_PUBLIC_USE_MOCK = enabled ? 'true' : 'false';
  writeEnvFile(env);
  
  console.log(`✅ Mock模式已${enabled ? '启用' : '禁用'}`);
  console.log(`📊 当前模式: ${enabled ? 'Mock数据' : '真实API'}`);
  
  if (!enabled) {
    console.log(`🔗 API地址: ${env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api'}`);
  }
  
  console.log('\n💡 请重启开发服务器以应用更改');
}

function showStatus() {
  const env = readEnvFile();
  const isMockEnabled = env.NEXT_PUBLIC_USE_MOCK !== 'false';
  
  console.log('📊 当前Mock配置状态:');
  console.log(`   模式: ${isMockEnabled ? 'Mock数据' : '真实API'}`);
  console.log(`   Mock开关: ${env.NEXT_PUBLIC_USE_MOCK || 'true'}`);
  console.log(`   API地址: ${env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api'}`);
  console.log(`   环境: ${env.NODE_ENV || 'development'}`);
}

function showHelp() {
  console.log('Mock模式切换工具');
  console.log('');
  console.log('用法:');
  console.log('  node scripts/toggle-mock.js [命令]');
  console.log('');
  console.log('命令:');
  console.log('  toggle    切换Mock模式 (默认)');
  console.log('  on        启用Mock模式');
  console.log('  off       禁用Mock模式');
  console.log('  status    显示当前状态');
  console.log('  help      显示帮助信息');
  console.log('');
  console.log('示例:');
  console.log('  node scripts/toggle-mock.js         # 切换模式');
  console.log('  node scripts/toggle-mock.js on      # 启用Mock');
  console.log('  node scripts/toggle-mock.js off     # 禁用Mock');
  console.log('  node scripts/toggle-mock.js status  # 查看状态');
}

// 主程序
const command = process.argv[2] || 'toggle';

switch (command) {
  case 'toggle':
    toggleMock();
    break;
  case 'on':
    setMockMode(true);
    break;
  case 'off':
    setMockMode(false);
    break;
  case 'status':
    showStatus();
    break;
  case 'help':
  case '--help':
  case '-h':
    showHelp();
    break;
  default:
    console.log(`❌ 未知命令: ${command}`);
    console.log('使用 "help" 查看可用命令');
    process.exit(1);
}
