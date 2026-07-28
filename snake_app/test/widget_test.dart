import 'dart:math';
import 'dart:ui';

import 'package:flutter_test/flutter_test.dart';
import 'package:snake_app/main.dart';

void main() {
  group('snake rendering helpers', () {
    test('interpolates body positions smoothly between ticks', () {
      final from = [const Point(10, 10), const Point(9, 10), const Point(8, 10)];
      final to = [const Point(11, 10), const Point(10, 10), const Point(9, 10)];

      final rendered = interpolateSnakePositions(from, to, 0.5);

      expect(rendered.first, const Offset(10.5, 10));
      expect(rendered[1], const Offset(9.5, 10));
      expect(rendered.last, const Offset(8.5, 10));
    });

    test('returns the target positions at the end of a movement step', () {
      final from = [const Point(10, 10), const Point(9, 10), const Point(8, 10)];
      final to = [const Point(11, 10), const Point(10, 10), const Point(9, 10)];

      final rendered = interpolateSnakePositions(from, to, 1.0);

      expect(rendered.first, const Offset(11, 10));
      expect(rendered[1], const Offset(10, 10));
      expect(rendered.last, const Offset(9, 10));
    });
  });
}
