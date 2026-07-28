// main.dart
//
// Classic Snake game built in Flutter.
//
// Architecture (kept intentionally simple, per plan):
//   - Single StatefulWidget (SnakeGame) holds all game state.
//   - StatefulWidget + setState is used for state management
//     (chosen over Provider/Riverpod for simplicity/learning).
//   - A Timer.periodic drives classic grid-based movement ticks.
//   - A CustomPainter draws the grid/snake/food efficiently.
//   - Both swipe gestures and on-screen D-pad buttons call the
//     same _changeDirection() method, so there's one source of
//     truth for input handling.

import 'dart:async';
import 'dart:math';
import 'package:flutter/material.dart';

void main() {
  runApp(const SnakeApp());
}

class SnakeApp extends StatelessWidget {
  const SnakeApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Snake',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        primarySwatch: Colors.green,
        scaffoldBackgroundColor: const Color(0xFF1B1B1B),
      ),
      home: const SnakeGame(),
    );
  }
}

enum Direction { up, down, left, right }

class SnakeGame extends StatefulWidget {
  const SnakeGame({super.key});

  @override
  State<SnakeGame> createState() => _SnakeGameState();
}

class _SnakeGameState extends State<SnakeGame> {
  static const int gridSize = 20; // 20x20 grid
  static const Duration tickDuration = Duration(milliseconds: 200);

  late List<Point<int>> _snake;
  late List<Point<int>> _previousSnake;
  late Point<int> _food;
  Direction _direction = Direction.right;
  Direction? _pendingDirection; // buffers input between ticks, avoids double-turn bug
  Timer? _timer;
  Timer? _renderTimer;
  int _score = 0;
  bool _isGameOver = false;
  DateTime _lastMovementTime = DateTime.now();

  final Random _random = Random();

  @override
  void initState() {
    super.initState();
    _startNewGame();
    _renderTimer = Timer.periodic(const Duration(milliseconds: 16), (_) {
      if (mounted) {
        setState(() {});
      }
    });
  }

  @override
  void dispose() {
    _timer?.cancel();
    _renderTimer?.cancel();
    super.dispose();
  }

  void _startNewGame() {
    _snake = [
      const Point(10, 10),
      const Point(9, 10),
      const Point(8, 10),
    ];
    _previousSnake = List<Point<int>>.from(_snake);
    _direction = Direction.right;
    _pendingDirection = null;
    _score = 0;
    _isGameOver = false;
    _placeFood();
    _lastMovementTime = DateTime.now();
    _timer?.cancel();
    _timer = Timer.periodic(tickDuration, (_) => _tick());
  }

  void _placeFood() {
    Point<int> newFood;
    do {
      newFood = Point(_random.nextInt(gridSize), _random.nextInt(gridSize));
    } while (_snake.contains(newFood)); // don't spawn food on the snake
    _food = newFood;
  }

  void _changeDirection(Direction newDirection) {
    // Prevent reversing directly into yourself (e.g. right -> left in one tick).
    final isOpposite =
        (_direction == Direction.up && newDirection == Direction.down) ||
        (_direction == Direction.down && newDirection == Direction.up) ||
        (_direction == Direction.left && newDirection == Direction.right) ||
        (_direction == Direction.right && newDirection == Direction.left);
    if (!isOpposite) {
      _pendingDirection = newDirection;
    }
  }

  void _tick() {
    if (_isGameOver) return;

    setState(() {
      _previousSnake = List<Point<int>>.from(_snake);
      _lastMovementTime = DateTime.now();

      if (_pendingDirection != null) {
        _direction = _pendingDirection!;
        _pendingDirection = null;
      }

      final head = _snake.first;
      Point<int> newHead;
      switch (_direction) {
        case Direction.up:
          newHead = Point(head.x, head.y - 1);
          break;
        case Direction.down:
          newHead = Point(head.x, head.y + 1);
          break;
        case Direction.left:
          newHead = Point(head.x - 1, head.y);
          break;
        case Direction.right:
          newHead = Point(head.x + 1, head.y);
          break;
      }

      // Wall collision.
      if (newHead.x < 0 ||
          newHead.x >= gridSize ||
          newHead.y < 0 ||
          newHead.y >= gridSize) {
        _endGame();
        return;
      }

      // Self collision.
      if (_snake.contains(newHead)) {
        _endGame();
        return;
      }

      _snake.insert(0, newHead);

      if (newHead == _food) {
        _score++;
        _placeFood(); // grow: don't remove tail this tick
      } else {
        _snake.removeLast();
      }
    });
  }

  void _endGame() {
    _isGameOver = true;
    _timer?.cancel();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            _buildScoreBar(),
            Expanded(
              child: GestureDetector(
                onVerticalDragUpdate: (details) {
                  if (details.delta.dy > 0) {
                    _changeDirection(Direction.down);
                  } else if (details.delta.dy < 0) {
                    _changeDirection(Direction.up);
                  }
                },
                onHorizontalDragUpdate: (details) {
                  if (details.delta.dx > 0) {
                    _changeDirection(Direction.right);
                  } else if (details.delta.dx < 0) {
                    _changeDirection(Direction.left);
                  }
                },
                child: Center(
                  child: AspectRatio(
                    aspectRatio: 1,
                    child: Container(
                      margin: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        border: Border.all(color: Colors.white24),
                      ),
                      child: Stack(
                        children: [
                          CustomPaint(
                            size: Size.infinite,
                            painter: _SnakePainter(
                              snake: _buildRenderedSnake(),
                              food: _food,
                              gridSize: gridSize,
                            ),
                          ),
                          if (_isGameOver) _buildGameOverOverlay(),
                        ],
                      ),
                    ),
                  ),
                ),
              ),
            ),
            _buildDPad(),
            const SizedBox(height: 12),
          ],
        ),
      ),
    );
  }

  List<Offset> _buildRenderedSnake() {
    final elapsed = DateTime.now().difference(_lastMovementTime);
    final progress = (elapsed.inMilliseconds / tickDuration.inMilliseconds)
        .clamp(0.0, 1.0);
    return interpolateSnakePositions(_previousSnake, _snake, progress);
  }

  Widget _buildScoreBar() {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 12),
      child: Text(
        'Score: $_score',
        style: const TextStyle(
          color: Colors.white,
          fontSize: 22,
          fontWeight: FontWeight.bold,
        ),
      ),
    );
  }

  Widget _buildGameOverOverlay() {
    return Container(
      color: Colors.black54,
      child: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text(
              'Game Over',
              style: TextStyle(
                color: Colors.white,
                fontSize: 28,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              'Score: $_score',
              style: const TextStyle(color: Colors.white70, fontSize: 18),
            ),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: () => setState(_startNewGame),
              child: const Text('Restart'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildDPad() {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        _dPadButton(Icons.keyboard_arrow_up, Direction.up),
        Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            _dPadButton(Icons.keyboard_arrow_left, Direction.left),
            const SizedBox(width: 48),
            _dPadButton(Icons.keyboard_arrow_right, Direction.right),
          ],
        ),
        _dPadButton(Icons.keyboard_arrow_down, Direction.down),
      ],
    );
  }

  Widget _dPadButton(IconData icon, Direction direction) {
    return IconButton(
      iconSize: 40,
      color: Colors.white,
      icon: Icon(icon),
      onPressed: () => _changeDirection(direction),
    );
  }
}

/// Draws the grid, snake, and food. A CustomPainter is used instead of
/// building hundreds of individual Container widgets, since that would
/// be inefficient to rebuild every tick.
class _SnakePainter extends CustomPainter {
  final List<Offset> snake;
  final Point<int> food;
  final int gridSize;

  _SnakePainter({
    required this.snake,
    required this.food,
    required this.gridSize,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final cellSize = size.width / gridSize;

    final bodyPaint = Paint()
      ..color = const Color(0xFF7CFC00)
      ..style = PaintingStyle.fill;
    final headPaint = Paint()
      ..color = const Color(0xFF2E8B57)
      ..style = PaintingStyle.fill;
    final foodPaint = Paint()..color = Colors.redAccent;

    for (int i = 0; i < snake.length; i++) {
      final point = snake[i];
      final rect = Rect.fromLTWH(
        point.dx * cellSize,
        point.dy * cellSize,
        cellSize,
        cellSize,
      );
      final rRect = RRect.fromRectAndRadius(
        rect,
        Radius.circular(cellSize * 0.28),
      );
      canvas.drawRRect(rRect, i == 0 ? headPaint : bodyPaint);
    }

    if (snake.isNotEmpty) {
      final head = snake.first;
      final eyePaint = Paint()..color = Colors.white;
      final pupilPaint = Paint()..color = Colors.black;
      final eyeOffset = Offset(cellSize * 0.16, cellSize * 0.16);
      canvas.drawCircle(head + eyeOffset, cellSize * 0.08, eyePaint);
      canvas.drawCircle(head + eyeOffset, cellSize * 0.04, pupilPaint);
    }

    final foodRect = Rect.fromLTWH(
      food.x * cellSize,
      food.y * cellSize,
      cellSize,
      cellSize,
    );
    canvas.drawOval(foodRect, foodPaint);
  }

  @override
  bool shouldRepaint(covariant _SnakePainter oldDelegate) {
    return true;
  }
}

List<Offset> interpolateSnakePositions(
  List<Point<int>> from,
  List<Point<int>> to,
  double progress,
) {
  final clampedProgress = progress.clamp(0.0, 1.0);
  final length = max(from.length, to.length);

  return List<Offset>.generate(length, (index) {
    final start = index < from.length ? from[index] : to[index];
    final end = index < to.length ? to[index] : from[index];

    return Offset(
      start.x + (end.x - start.x) * clampedProgress,
      start.y + (end.y - start.y) * clampedProgress,
    );
  });
}