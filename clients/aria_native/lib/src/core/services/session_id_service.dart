import 'dart:math';

import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';


class SessionIdService extends ChangeNotifier {
  String? _sessionId;
  String? get sessionId => _sessionId;
  static const String _key = 'aria_session_id';

  Future<void> load() async {
    final prefs = await SharedPreferences.getInstance();
    final existing = prefs.getString(_key);
    if (existing != null && existing.isNotEmpty) {
      _sessionId = existing;
      notifyListeners();
      return;
    }
    final generated = _generateSessionId();
    await prefs.setString(_key, generated);
    _sessionId = generated;
    notifyListeners();
  }

  Future<void> reset() async {
    final prefs = await SharedPreferences.getInstance();
    final generated = _generateSessionId();
    await prefs.setString(_key, generated);
    _sessionId = generated;
    notifyListeners();
  }

  String _generateSessionId() {
    final random = Random.secure();
    final bytes = List<int>.generate(16, (_) => random.nextInt(256));
    return bytes.map((b) => b.toRadixString(16).padLeft(2, '0')).join();
  }
}
