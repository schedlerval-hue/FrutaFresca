INSERT INTO produtos
(codigo, nome, descricao, custo, preco, estoque, imagem)
VALUES
('001', 'Morango', 'Morangos frescos e selecionados.', 6.00, 10.00, 30, 'morango.jpg');

INSERT INTO produtos
(codigo, nome, descricao, custo, preco, estoque, imagem)
VALUES
('002', 'Uva', 'Uvas frescas e doces.', 4.00, 8.00, 30, 'uva.jpg');

INSERT INTO produtos
(codigo, nome, descricao, custo, preco, estoque, imagem)
VALUES
('003', 'Laranja', 'Laranjas frescas e suculentas.', 3.00, 6.00, 30, 'laranja.jpg');
UPDATE produtos
SET preco = 45.00
WHERE codigo = '001';

UPDATE produtos
SET preco = 35.00
WHERE codigo = '002';

UPDATE produtos
SET preco = 8.99
WHERE codigo = '003';