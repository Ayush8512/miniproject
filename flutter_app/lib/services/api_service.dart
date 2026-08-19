import 'dart:convert';
import 'package:http/http.dart' as http;

class ApiService {
  static final ApiService _instance = ApiService._internal();
  factory ApiService() => _instance;
  ApiService._internal();

  String baseUrl = 'http://10.0.2.2:8000';
  String? _token;
  
  Map<String, String> get _headers {
    return {
      'Content-Type': 'application/json',
      if (_token != null) 'Authorization': 'Bearer $_token',
    };
  }

  Future<Map<String, dynamic>> login(String rollNo, String password, String deviceId) async {
    final response = await http.post(
      Uri.parse('$baseUrl/auth/login'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'roll_no': rollNo,
        'password': password,
        'device_id': deviceId,
      }),
    );
    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      _token = data['access_token'];
      return data;
    } else if (response.statusCode == 403) {
        throw Exception('403');
    } else {
      throw Exception('Login failed: ${response.statusCode}');
    }
  }

  Future<List<Map<String, dynamic>>> getTodaySchedule(String rollNo) async {
    final response = await http.get(
      Uri.parse('$baseUrl/attendance/today_schedule/$rollNo'),
      headers: _headers,
    );
    if (response.statusCode == 200) {
      return List<Map<String, dynamic>>.from(jsonDecode(response.body));
    } else {
      throw Exception('Failed to load schedule');
    }
  }

  Future<Map<String, dynamic>> verifyAttendance(Map<String, dynamic> payload) async {
    final response = await http.post(
      Uri.parse('$baseUrl/attendance/verify'),
      headers: _headers,
      body: jsonEncode(payload),
    );
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception('Attendance verification failed');
    }
  }
}
