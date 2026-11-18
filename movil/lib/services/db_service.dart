// SQLite (sqflite) persistence for FotoPendiente records.

import 'package:path/path.dart' as p;
import 'package:path_provider/path_provider.dart';
import 'package:sqflite/sqflite.dart';

import '../models/foto_pendiente.dart';

const String _table = 'fotos_pendientes';
Database? _database;

/// Opens (once) the app-localSQLite database and creates the schema.
Future<Database> _open() async {
  final existing = _database;
  if (existing != null && existing.isOpen) return existing;

  final documents = await getApplicationDocumentsDirectory();
  final path = p.join(documents.path, 'supervisor_ia.db');
  final database = await openDatabase(
    path,
    version: 1,
    onCreate: (db, _) async {
      await db.execute('''
        CREATE TABLE $_table (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          path TEXT,
          obra_id TEXT,
          timestamp TEXT,
          sincronizada INTEGER DEFAULT 0
        )
      ''');
    },
  );
  _database = database;
  return database;
}

/// Llamar desde main() antes de runApp.
Future<void> inicializarDb() async {
  await _open();
}

/// Inserta una foto y devuelve el id autogenerado.
Future<int> insertarFoto(FotoPendiente foto) async {
  final db = await _open();
  return db.insert(_table, foto.toMap());
}

/// Devuelve solo las fotos todavía no sincronizadas, más recientes primero.
Future<List<FotoPendiente>> obtenerFotosPendientes() async {
  final db = await _open();
  final rows = await db.query(
    _table,
    where: 'sincronizada = ?',
    whereArgs: [0],
    orderBy: 'timestamp DESC',
  );
  return rows.map(FotoPendiente.fromMap).toList();
}

/// Marca una foto como subida al backend.
Future<int> marcarComoSincronizada(int id) async {
  final db = await _open();
  return db.update(
    _table,
    {'sincronizada': 1},
    where: 'id = ?',
    whereArgs: [id],
  );
}
