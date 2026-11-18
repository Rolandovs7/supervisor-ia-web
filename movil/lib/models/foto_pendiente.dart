/// A photo captured offline that still needs to be uploaded to the backend.
class FotoPendiente {
  const FotoPendiente({
    this.id,
    required this.path,
    required this.timestamp,
    this.obraId,
    this.sincronizada = false,
  });

  final int? id;
  final String path;
  final String? obraId;
  final DateTime timestamp;
  final bool sincronizada;

  Map<String, dynamic> toMap() => {
        'path': path,
        'obra_id': obraId,
        'timestamp': timestamp.toIso8601String(),
        'sincronizada': sincronizada ? 1 : 0,
      };

  factory FotoPendiente.fromMap(Map<String, dynamic> map) => FotoPendiente(
        id: map['id'] as int?,
        path: map['path'] as String,
        obraId: map['obra_id'] as String?,
        timestamp: DateTime.parse(map['timestamp'] as String),
        sincronizada: (map['sincronizada'] as int?) == 1,
      );
}
