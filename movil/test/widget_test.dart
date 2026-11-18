// Smoke test for the initial screen.

import 'package:flutter_test/flutter_test.dart';

import 'package:movil/main.dart';

void main() {
  testWidgets('Muestra el formulario de login', (WidgetTester tester) async {
    await tester.pumpWidget(const SupervisorApp());

    expect(find.text('Ingresar'), findsOneWidget);
    expect(find.text('Email'), findsOneWidget);
    expect(find.text('Password'), findsOneWidget);
  });
}
