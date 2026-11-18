// Camera screen: captures a photo and queues it for later upload.

import 'dart:io';

import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:path/path.dart' as p;
import 'package:path_provider/path_provider.dart';

import '../models/foto_pendiente.dart';
import '../services/db_service.dart';
import '../services/sync_service.dart';

class CapturaScreen extends StatefulWidget {
  const CapturaScreen({super.key});

  @override
  State<CapturaScreen> createState() => _CapturaScreenState();
}

class _CapturaScreenState extends State<CapturaScreen> {
  final ImagePicker _picker = ImagePicker();
  late Future<List<FotoPendiente>> _fotos;
  bool _tomando = false;
  bool _sincronizando = false;

  @override
  void initState() {
    super.initState();
    _fotos = obtenerFotosPendientes();
  }

  void _recargar() {
    if (!mounted) return;
    setState(() {
      _fotos = obtenerFotosPendientes();
    });
  }

  void _avisar(String mensaje) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(mensaje)),
    );
  }

  Future<void> _tomarFoto() async {
    setState(() => _tomando = true);
    try {
      final XFile? foto = await _picker.pickImage(
        source: ImageSource.camera,
        imageQuality: 85,
      );
      if (foto == null) return;

      final directorio = await getApplicationDocumentsDirectory();
      final nombre = 'foto_${DateTime.now().millisecondsSinceEpoch}.jpg';
      final destino = File(p.join(directorio.path, nombre));
      await destino.writeAsBytes(await foto.readAsBytes());

      await insertarFoto(
        FotoPendiente(path: destino.path, timestamp: DateTime.now()),
      );
      _recargar();
      _avisar('Foto guardada localmente. Pendiente de sincronizar');
    } catch (error) {
      _avisar('No se pudo guardar la foto: $error');
    } finally {
      if (mounted) {
        setState(() => _tomando = false);
      }
    }
  }

  Future<void> _sincronizar() async {
    setState(() => _sincronizando = true);
    try {
      final enviadas = await sincronizarFotos();
      _recargar();
      if (enviadas > 0) {
        _avisar('$enviadas foto(s) sincronizada(s) correctamente.');
      } else {
        _avisar('No hay conexión o no hay fotos pendientes.');
      }
    } catch (error) {
      _avisar(
        'No se pudo sincronizar: ${error.toString().replaceFirst('StateError: ', '')}',
      );
    } finally {
      if (mounted) {
        setState(() => _sincronizando = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Captura de evidencia'),
        actions: [
          IconButton(
            onPressed: _recargar,
            icon: const Icon(Icons.refresh),
            tooltip: 'Actualizar lista',
          ),
        ],
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              ElevatedButton.icon(
                onPressed: _tomando ? null : _tomarFoto,
                icon: _tomando
                    ? const SizedBox(
                        height: 18,
                        width: 18,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Icon(Icons.camera_alt),
                label: const Text('Tomar Foto'),
              ),
              const SizedBox(height: 12),
              OutlinedButton.icon(
                onPressed: _sincronizando ? null : _sincronizar,
                icon: _sincronizando
                    ? const SizedBox(
                        height: 18,
                        width: 18,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Icon(Icons.cloud_upload_outlined),
                label: const Text('Sincronizar Ahora'),
              ),
              const SizedBox(height: 24),
              Text(
                'Fotos pendientes',
                style: Theme.of(context).textTheme.titleMedium,
              ),
              const SizedBox(height: 8),
              Expanded(
                child: FutureBuilder<List<FotoPendiente>>(
                  future: _fotos,
                  builder: (context, snapshot) {
                    if (snapshot.connectionState == ConnectionState.waiting) {
                      return const Center(child: CircularProgressIndicator());
                    }
                    if (snapshot.hasError) {
                      return Center(child: Text('Error: ${snapshot.error}'));
                    }
                    final fotos = snapshot.data ?? const <FotoPendiente>[];
                    if (fotos.isEmpty) {
                      return const Center(
                        child: Text('No hay fotos pendientes.'),
                      );
                    }
                    return ListView.separated(
                      itemCount: fotos.length,
                      separatorBuilder: (_, _) => const Divider(height: 1),
                      itemBuilder: (context, index) {
                        final foto = fotos[index];
                        return ListTile(
                          leading: const Icon(Icons.image_outlined),
                          title: Text(p.basename(foto.path)),
                          subtitle: Text(foto.timestamp.toLocal().toString()),
                        );
                      },
                    );
                  },
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
