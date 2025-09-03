# MongoDB Migration Guide: Local to Atlas

This guide will help you migrate your UPS Monitoring System from local MongoDB to MongoDB Atlas.

## 🎯 Overview

We'll be migrating your local MongoDB database (`UPS_DATA_MONITORING`) with collections:
- `upsdata` - UPS system data
- `ups_predictions` - ML predictions
- `alerts` - System alerts

## 📋 Prerequisites

1. ✅ MongoDB Atlas account with cluster access
2. ✅ Connection string: `mongodb+srv://vamsidulam11:vamsi2005121@cluster0.4kq3vjn.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0`
3. ✅ Local MongoDB running with data
4. ✅ Python environment with `pymongo` installed

## 🚀 Migration Steps

### Step 1: Update Connection Strings

First, update all Python files to use Atlas connection string:

```bash
cd backend
python update_connection_strings.py
```

This will update all `.py` files to use the Atlas connection string instead of localhost.

### Step 2: Run Data Migration

Migrate your data from local MongoDB to Atlas:

```bash
cd backend
python migrate_to_atlas.py
```

This script will:
- Connect to both local and Atlas databases
- Export all data from local collections
- Import data to Atlas collections
- Create proper indexes
- Update configuration files

### Step 3: Test the Migration

Verify that your application works with Atlas:

```bash
# Test basic connectivity
python check_status.py

# Test data access
python check_current_status.py

# Test predictions
python check_predictions.py
```

### Step 4: Update Docker Configuration

After successful migration, update your `docker-compose.yml`:

```yaml
# Comment out or remove the mongodb service
# mongodb:
#   image: mongo:7.0
#   ...

# Update backend environment variables
backend:
  environment:
    - MONGODB_URI=mongodb+srv://vamsidulam11:vamsi2005121@cluster0.4kq3vjn.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0
    - DB_NAME=UPS_DATA_MONITORING
```

## 🔍 Verification Checklist

- [ ] All Python files updated with Atlas connection string
- [ ] Data successfully migrated to Atlas
- [ ] Indexes created on Atlas collections
- [ ] Application connects to Atlas successfully
- [ ] All functionality works with Atlas database
- [ ] Local MongoDB can be stopped

## 📊 Expected Results

After migration, you should see:
- All your data in MongoDB Atlas
- Same database structure and indexes
- Application working identically to before
- Better performance and reliability
- Cloud-based database management

## 🚨 Troubleshooting

### Connection Issues
- Verify Atlas cluster is running
- Check network access and IP whitelist
- Ensure connection string is correct

### Data Issues
- Check if local MongoDB has data
- Verify collection names match
- Check for permission issues

### Application Issues
- Restart application after migration
- Check environment variables
- Verify connection string in code

## 📝 Post-Migration

1. **Monitor Performance**: Watch for any performance changes
2. **Backup Strategy**: Set up regular Atlas backups
3. **Scaling**: Consider Atlas auto-scaling features
4. **Security**: Review Atlas security settings

## 🔗 Useful Commands

```bash
# Check local MongoDB status
docker ps | grep mongodb

# Check Atlas connection
python -c "from pymongo import MongoClient; client = MongoClient('your_atlas_uri'); print('Connected:', client.admin.command('ping'))"

# View migration logs
tail -f migration.log
```

## 📞 Support

If you encounter issues:
1. Check the migration script output
2. Verify Atlas cluster status
3. Review MongoDB logs
4. Test with simple connection script

---

**Migration completed successfully! 🎉**

Your UPS Monitoring System is now running on MongoDB Atlas with improved reliability and scalability.
