CREATE TABLE orders (
    id BIGINT NOT NULL AUTO_INCREMENT,
    product_id BIGINT NOT NULL,
    quantity INT NOT NULL,
    status VARCHAR(32) NOT NULL,
    PRIMARY KEY (id),
    CONSTRAINT chk_orders_product_id_positive CHECK (product_id > 0),
    CONSTRAINT chk_orders_quantity_positive CHECK (quantity > 0)
);
