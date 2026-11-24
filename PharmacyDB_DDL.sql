IF DB_ID(N'PharmacyDB') IS NULL
BEGIN
    CREATE DATABASE PharmacyDB;
END;
GO

USE PharmacyDB;
GO

CREATE TABLE Branch (
    Branch_ID     INT IDENTITY(1,1) PRIMARY KEY,
    Branch_Name   NVARCHAR(100) NOT NULL,
    Location      NVARCHAR(200) NOT NULL,
    Phone         NVARCHAR(30)  NULL
);
GO

CREATE TABLE Medicine (
    Medicine_ID    INT IDENTITY(1,1) PRIMARY KEY,
    Medicine_Name  NVARCHAR(100) NOT NULL,
    Barcode        NVARCHAR(50)  NOT NULL UNIQUE,
    Price          DECIMAL(10,2) NOT NULL CHECK (Price >= 0)
);
GO

CREATE TABLE Supplier (
    Supplier_ID  INT IDENTITY(1,1) PRIMARY KEY,
    Name         NVARCHAR(100) NOT NULL,
    Phone        NVARCHAR(30)  NULL,
    Address      NVARCHAR(200) NULL,
    Medicine_ID  INT NULL,
    CONSTRAINT FK_Supplier_Medicine FOREIGN KEY (Medicine_ID)
        REFERENCES Medicine(Medicine_ID)
);
GO

CREATE TABLE Customer (
    Customer_ID  INT IDENTITY(1,1) PRIMARY KEY,
    Name         NVARCHAR(100) NOT NULL,
    Phone        NVARCHAR(30)  NULL,
    Email        NVARCHAR(100) NULL UNIQUE
);
GO

CREATE TABLE Employee (
    Employee_ID  INT IDENTITY(1,1) PRIMARY KEY,
    Name         NVARCHAR(100) NOT NULL,
    Role         NVARCHAR(50)  NOT NULL,
    Salary       DECIMAL(10,2) NOT NULL CHECK (Salary >= 0),
    Branch_ID    INT NOT NULL,
    CONSTRAINT FK_Employee_Branch FOREIGN KEY (Branch_ID)
        REFERENCES Branch(Branch_ID)
);
GO

CREATE TABLE Inventory (
    Inventory_ID  INT IDENTITY(1,1) PRIMARY KEY,
    Batch_Number  NVARCHAR(50) NOT NULL,
    Quantity      INT NOT NULL DEFAULT 0 CHECK (Quantity >= 0),
    Expiry_Date   DATE NOT NULL,
    Branch_ID     INT NOT NULL,
    CONSTRAINT FK_Inventory_Branch FOREIGN KEY (Branch_ID)
        REFERENCES Branch(Branch_ID)
);
GO

CREATE TABLE Purchase (
    Purchase_ID    INT IDENTITY(1,1) PRIMARY KEY,
    Purchase_Date  DATE NOT NULL DEFAULT GETDATE(),
    Total_Cost     DECIMAL(12,2) NOT NULL CHECK (Total_Cost >= 0)
);
GO

CREATE TABLE Sale (
    Sale_ID         INT IDENTITY(1,1) PRIMARY KEY,
    Sale_Date       DATE NOT NULL DEFAULT GETDATE(),
    Amount          DECIMAL(12,2) NOT NULL CHECK (Amount >= 0),
    Payment_Method  NVARCHAR(30) NOT NULL
        CHECK (Payment_Method IN (N'Cash', N'Card', N'Insurance', N'Online')),
    Customer_ID     INT NOT NULL,
    Employee_ID     INT NOT NULL,
    CONSTRAINT FK_Sale_Customer FOREIGN KEY (Customer_ID)
        REFERENCES Customer(Customer_ID),
    CONSTRAINT FK_Sale_Employee FOREIGN KEY (Employee_ID)
        REFERENCES Employee(Employee_ID)
);
GO

CREATE TABLE Prescription (
    Prescription_ID    INT IDENTITY(1,1) PRIMARY KEY,
    Doctor_Name        NVARCHAR(100) NOT NULL,
    Diagnosis          NVARCHAR(200) NULL,
    Prescription_Date  DATE NOT NULL DEFAULT GETDATE(),
    Sale_ID            INT NULL,
    CONSTRAINT FK_Prescription_Sale FOREIGN KEY (Sale_ID)
        REFERENCES Sale(Sale_ID)
);
GO

CREATE TABLE Purchase_Medicine (
    Purchase_ID  INT NOT NULL,
    Medicine_ID  INT NOT NULL,
    Quantity     INT NOT NULL CHECK (Quantity > 0),
    CONSTRAINT PK_Purchase_Medicine PRIMARY KEY (Purchase_ID, Medicine_ID),
    CONSTRAINT FK_PM_Purchase FOREIGN KEY (Purchase_ID)
        REFERENCES Purchase(Purchase_ID),
    CONSTRAINT FK_PM_Medicine FOREIGN KEY (Medicine_ID)
        REFERENCES Medicine(Medicine_ID)
);
GO

CREATE TABLE Inventory_Medicine (
    Inventory_ID  INT NOT NULL,
    Medicine_ID   INT NOT NULL,
    CONSTRAINT PK_Inventory_Medicine PRIMARY KEY (Inventory_ID, Medicine_ID),
    CONSTRAINT FK_IM_Inventory FOREIGN KEY (Inventory_ID)
        REFERENCES Inventory(Inventory_ID),
    CONSTRAINT FK_IM_Medicine FOREIGN KEY (Medicine_ID)
        REFERENCES Medicine(Medicine_ID)
);
GO

CREATE TABLE Sale_Medicine (
    Sale_ID      INT NOT NULL,
    Medicine_ID  INT NOT NULL,
    Quantity     INT NOT NULL CHECK (Quantity > 0),
    CONSTRAINT PK_Sale_Medicine PRIMARY KEY (Sale_ID, Medicine_ID),
    CONSTRAINT FK_SM_Sale FOREIGN KEY (Sale_ID)
        REFERENCES Sale(Sale_ID),
    CONSTRAINT FK_SM_Medicine FOREIGN KEY (Medicine_ID)
        REFERENCES Medicine(Medicine_ID)
);
GO

CREATE TABLE Prescription_Sale (
    Prescription_ID  INT NOT NULL,
    Sale_ID          INT NOT NULL,
    CONSTRAINT PK_Prescription_Sale PRIMARY KEY (Prescription_ID, Sale_ID),
    CONSTRAINT FK_PS_Prescription FOREIGN KEY (Prescription_ID)
        REFERENCES Prescription(Prescription_ID),
    CONSTRAINT FK_PS_Sale FOREIGN KEY (Sale_ID)
        REFERENCES Sale(Sale_ID)
);
GO
