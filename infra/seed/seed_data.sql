-- Seed data: fictional toy store
INSERT INTO products (name, category, price, stock) VALUES
  ('Blocos Magnéticos XL', 'construção', 129.90, 45),
  ('Quebra-Cabeça 500 Peças', 'educativo', 59.90, 80),
  ('Kit Robótica Iniciante', 'STEM', 249.90, 20),
  ('Pelúcia Urso Gigante', 'pelúcias', 89.90, 60),
  ('Carrinho Controle Remoto', 'eletrônicos', 179.90, 30);

INSERT INTO orders (product_id, quantity, total, status, created_at) VALUES
  (1, 2, 259.80, 'entregue', NOW() - INTERVAL '10 days'),
  (3, 1, 249.90, 'enviado', NOW() - INTERVAL '3 days'),
  (2, 3, 179.70, 'entregue', NOW() - INTERVAL '7 days'),
  (5, 1, 179.90, 'pendente', NOW() - INTERVAL '1 day'),
  (4, 2, 179.80, 'entregue', NOW() - INTERVAL '5 days');

INSERT INTO reviews (product_id, rating, comment) VALUES
  (1, 5, 'Perfeito para crianças de 4 anos. Encaixe fácil e peças grandes.'),
  (1, 4, 'Ótima qualidade, mas poderia ter mais variedade de cores.'),
  (3, 5, 'Meu filho ficou viciado no kit. Vale cada centavo.'),
  (3, 3, 'Difícil montar sem ajuda de adulto. Instruções confusas.'),
  (2, 4, 'Entreteve a família o fim de semana todo.'),
  (5, 2, 'Bateria dura apenas 30 minutos. Decepcionante.'),
  (4, 5, 'Pelúcia muito macia. Criança adora.');
