const express = require('express');
const cors = require('cors');
const app = express();
const port = 8080;

app.use(cors());
app.use(express.json());

// Mock user data
const mockUser = {
  id: 1,
  telegram_id: 123456789,
  username: "test_user",
  first_name: "Test",
  last_name: "User",
  language_code: "ru",
  balance_kopeks: 50000, // 500 рублей
  is_premium: false,
  created_at: "2024-01-01T00:00:00Z"
};

// Mock subscription data
const mockSubscription = {
  id: 1,
  user_id: 1,
  status: "active",
  expires_at: "2024-12-31T23:59:59Z",
  traffic_limit_bytes: null, // unlimited
  traffic_used_bytes: 1024 * 1024 * 1024 * 5, // 5GB used
  device_limit: 5,
  devices_count: 2,
  created_at: "2024-01-01T00:00:00Z"
};

// Mock devices
const mockDevices = [
  {
    id: 1,
    name: "iPhone 15",
    config_id: "device_1_config",
    created_at: "2024-01-01T00:00:00Z",
    last_seen: "2024-03-31T20:00:00Z"
  },
  {
    id: 2,
    name: "MacBook Pro",
    config_id: "device_2_config", 
    created_at: "2024-01-15T00:00:00Z",
    last_seen: "2024-03-31T21:00:00Z"
  }
];

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// Cabinet API endpoints
app.get('/cabinet/auth/me', (req, res) => {
  res.json({
    user: mockUser,
    subscription: mockSubscription
  });
});

app.get('/cabinet/user/profile', (req, res) => {
  res.json(mockUser);
});

app.get('/cabinet/subscription/current', (req, res) => {
  res.json(mockSubscription);
});

app.get('/cabinet/devices', (req, res) => {
  res.json({
    devices: mockDevices,
    total: mockDevices.length,
    limit: mockSubscription.device_limit
  });
});

app.get('/cabinet/balance', (req, res) => {
  res.json({
    balance_kopeks: mockUser.balance_kopeks,
    balance_rub: mockUser.balance_kopeks / 100
  });
});

// Payment methods
app.get('/cabinet/payments/methods', (req, res) => {
  res.json({
    methods: [
      {
        id: 'yookassa',
        name: 'ЮKassa',
        icon: '💳',
        min_amount_kopeks: 10000,
        max_amount_kopeks: 1500000,
        currency: 'RUB'
      },
      {
        id: 'stars',
        name: 'Telegram Stars',
        icon: '⭐',
        min_amount_kopeks: 5000,
        max_amount_kopeks: 500000,
        currency: 'XTR'
      }
    ]
  });
});

// Tariffs
app.get('/cabinet/tariffs', (req, res) => {
  res.json({
    tariffs: [
      {
        id: 1,
        name: "Базовый",
        duration_days: 30,
        price_kopeks: 29900,
        traffic_limit_bytes: null,
        device_limit: 3,
        description: "Безлимитный трафик, 3 устройства"
      },
      {
        id: 2,
        name: "Премиум",
        duration_days: 30,
        price_kopeks: 49900,
        traffic_limit_bytes: null,
        device_limit: 5,
        description: "Безлимитный трафик, 5 устройств"
      }
    ]
  });
});

// Referral stats
app.get('/cabinet/referral/stats', (req, res) => {
  res.json({
    total_referrals: 12,
    active_referrals: 8,
    total_earned_kopeks: 24000,
    available_for_withdrawal_kopeks: 18000,
    referral_link: `https://t.me/test_bot?start=ref_${mockUser.id}`
  });
});

// Catch all other routes
app.use('*', (req, res) => {
  res.status(404).json({ error: 'Endpoint not implemented in mock server' });
});

// Start server
app.listen(port, () => {
  console.log(`🚀 Mock API server running at http://localhost:${port}`);
  console.log(`📱 Frontend should now work with mock data`);
  console.log(`🔗 Health check: http://localhost:${port}/health`);
});
