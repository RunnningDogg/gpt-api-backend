CREATE TABLE IF NOT EXISTS `user`(
   `id` INT UNSIGNED AUTO_INCREMENT,
   `name` VARCHAR(100) NOT NULL,
   `password`  VARCHAR(512) NOT NULL,
   `email` VARCHAR(512) NOT NULL,
   `create_time` datetime,
   `update_time` datetime,
   `status` int COMMENT "用户状态 注册 0 正常1 封禁2 删除3 ",
   `user_role` int COMMENT "用户角色 0 普通用户，1是admin用户",
   `is_delete` int COMMENT "未删除0 删除1",
   PRIMARY KEY ( `id` )
)ENGINE=InnoDB DEFAULT CHARSET=utf8;


INSERT INTO user (name, password, email, create_time, update_time, status, user_role, is_delete)
VALUES ('terry', '123456', 'john@example.com', NOW(), NOW(), 1, 0 , 0);

INSERT INTO user (name, password, email, create_time, update_time, status, user_role, is_delete)
VALUES ('tony', '123456asd', 'tony@example.com', NOW(), NOW(), 1, 1 , 0);

INSERT INTO user (name, password, email, create_time, update_time, status, user_role, is_delete)
VALUES ('liang', '123456', 'liang@example.com', NOW(), NOW(), 1, 1 , 0);

INSERT INTO user (name, password, email, create_time, update_time, status, user_role, is_delete)
VALUES ('bryant', '123456', 'bryant@example.com', NOW(), NOW(), 1, 0 , 0);

INSERT INTO user (name, password, email, create_time, update_time, status, user_role, is_delete)
VALUES ('jiayin', '123456asd', 'tony@example.com', NOW(), NOW(), 1, 1 , 0);

INSERT INTO user (name, password, email, create_time, update_time, status, user_role, is_delete)
VALUES ('gogo', '123456asd', 'tony@example.com', NOW(), NOW(), 1, 1 , 0);