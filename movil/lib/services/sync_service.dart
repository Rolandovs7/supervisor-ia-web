// Uploads pending photos when connectivity is available.

import 'dart:io';

import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:http/http.dart' as http;
import 'package:path/path.dart' as p;

import '../config.dart';
import 'auth_service.dart';
import 'db_service.dart';

/// Sube cada foto pendiente y devuelve cuántas se sincronizaron.
Future<int> sincronizarFotos() async {
  final conexiones = await Connectivity().checkConnectivity();
  if (conexiones.every((resultado) => resultado == ConnectivityResult.none)) {
    return 0;
  }

  final fotos = await obtenerFotosPendientes();
  if (fotos.isEmpty) return 0;

  final token = await obtenerToken();
  if (token == null) {
    throw StateError('No hay sesión activa. Ingresa nuevamente.');
  }

  var sincronizadas = 0;
  for (final foto in fotos) {
    final archivo = File(foto.path);
    if (!archivo.existsSync()) continue;

    final request = http.MultipartRequest('POST', Uri.parse('$apiUrl/upload'))
      ..headers['Authorization'] = 'Bearer $token';
    if (foto.obraId != null && foto.obraId!.isNotEmpty) {
      request.fields['obra_id'] = foto.obraId!;
    }
    request.files.add(
      await http.MultipartFile.fromPath(
        'file',
        archivo.path,
        filename: p.basename(archivo.path),
      ),
    );

    final response = await request.send();
    if (response.statusCode == 200) {
      await marcarComoSincronizada(foto.id!);
      sincronizadas++;
    }
    await response.stream.drain<void>();
  }
  return sincronizadas;
}
