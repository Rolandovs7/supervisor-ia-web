// Stores the JWT shared by login and sync.

import 'package:shared_preferences/shared_preferences.dart';

const String _tokenKey = 'supervisor_ia_token';

Future<void> guardarToken(String token) async {
  final prefs = await SharedPreferences.getInstance();
  await prefs.setString(_tokenKey, token);
}

Future<String?> obtenerToken() async {
  final prefs = await SharedPreferences.getInstance();
  return prefs.getString(_tokenKey);
}

Future<void> limpiarToken() async {
  final prefs = await SharedPreferences.getInstance();
  await prefs.remove(_tokenKey);
}
