const path = require('path');
require('dotenv').config({ path: path.resolve(__dirname, '..', '.env') });

module.exports = {
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/trains',
    NEXT_PUBLIC_TENSORBOARD_URL: process.env.TENSORBOARD_URL || 'http://trainvision-sv1:6006/'
  }
}