import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../services/api_service.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({Key? key}) : super(key: key);

  @override
  _HomeScreenState createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  List<Map<String, dynamic>> _schedule = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _fetchSchedule();
  }

  Future<void> _fetchSchedule() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      String? rollNo = prefs.getString('roll_no');
      if (rollNo != null) {
        final data = await ApiService().getTodaySchedule(rollNo);
        setState(() {
          _schedule = data;
          _isLoading = false;
        });
      }
    } catch (e) {
      setState(() => _isLoading = false);
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Failed to fetch schedule')));
    }
  }

  void _logout() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('roll_no');
    if (mounted) Navigator.pushReplacementNamed(context, '/login');
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Today\'s Schedule'),
        actions: [
          IconButton(icon: const Icon(Icons.logout), onPressed: _logout),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _schedule.isEmpty
              ? const Center(child: Text('No classes scheduled for today.'))
              : ListView.builder(
                  itemCount: _schedule.length,
                  itemBuilder: (ctx, i) {
                    final item = _schedule[i];
                    // Example mock logic for active class
                    bool isActive = i == 0; 
                    return Card(
                      shape: isActive
                          ? RoundedRectangleBorder(
                              side: const BorderSide(color: Colors.green, width: 2),
                              borderRadius: BorderRadius.circular(8),
                            )
                          : null,
                      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                      child: ListTile(
                        contentPadding: const EdgeInsets.all(16),
                        title: Text('${item['subject']} - ${item['room_name']}', style: const TextStyle(fontWeight: FontWeight.bold)),
                        subtitle: Text('${item['start_time']} - ${item['end_time']}\nTeacher: ${item['teacher_email']}'),
                        trailing: isActive
                            ? ElevatedButton(
                                onPressed: () {
                                  Navigator.pushNamed(context, '/attendance', arguments: item);
                                },
                                child: const Text('Mark Attendance'),
                              )
                            : null,
                      ),
                    );
                  },
                ),
    );
  }
}
