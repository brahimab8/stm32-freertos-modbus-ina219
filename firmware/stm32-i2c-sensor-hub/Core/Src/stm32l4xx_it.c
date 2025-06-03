/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file    stm32l4xx_it.c
  * @brief   Interrupt Service Routines.
  ******************************************************************************
  * @attention
  *
  * Copyright (c) 2025 STMicroelectronics.
  * All rights reserved.
  *
  * This software is licensed under terms that can be found in the LICENSE file
  * in the root directory of this software component.
  * If no LICENSE file comes with this software, it is provided AS-IS.
  *
  ******************************************************************************
  */
/* USER CODE END Header */

/* Includes ------------------------------------------------------------------*/
#include "main.h"
#include "stm32l4xx_it.h"
/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */
#include <stdio.h>
#include <string.h>
/* USER CODE END Includes */

/* Private typedef -----------------------------------------------------------*/
/* USER CODE BEGIN TD */

/* USER CODE END TD */

/* Private define ------------------------------------------------------------*/
/* USER CODE BEGIN PD */

/* USER CODE END PD */

/* Private macro -------------------------------------------------------------*/
/* USER CODE BEGIN PM */

/* USER CODE END PM */

/* Private variables ---------------------------------------------------------*/
/* USER CODE BEGIN PV */

/* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/
/* USER CODE BEGIN PFP */

/* USER CODE END PFP */

/* Private user code ---------------------------------------------------------*/
/* USER CODE BEGIN 0 */
extern UART_HandleTypeDef huart2; // for debug output

static void print_uint32_hex(uint32_t v)
{
    char buf[11];
    snprintf(buf, sizeof(buf), "0x%08lX", (unsigned long)v);
    HAL_UART_Transmit(&huart2, (uint8_t*)buf, (uint16_t)strlen(buf), HAL_MAX_DELAY);
}

void HardFault_Handler_C(uint32_t *stacked_frame)
{
    // stacked_frame[6] == stacked PC
    uint32_t fault_pc = stacked_frame[6];
    uint32_t stacked_lr = stacked_frame[5];
    uint32_t stacked_sp = (uint32_t)stacked_frame;

    // Read System Control Block registers
    uint32_t cfsr = SCB->CFSR;  // Configurable Fault Status Register
    uint32_t hfsr = SCB->HFSR;  // HardFault Status Register

    // Print a header
    const char *msg1 = "\r\n--- HARDFAULT ---\r\n";
    HAL_UART_Transmit(&huart2, (uint8_t*)msg1, (uint16_t)strlen(msg1), HAL_MAX_DELAY);

    // Print stacked PC
    const char *pc_text = " stacked PC = ";
    HAL_UART_Transmit(&huart2, (uint8_t*)pc_text, (uint16_t)strlen(pc_text), HAL_MAX_DELAY);
    print_uint32_hex(fault_pc);
    const char *crlf = "\r\n";
    HAL_UART_Transmit(&huart2, (uint8_t*)crlf, (uint16_t)strlen(crlf), HAL_MAX_DELAY);

    // Print stacked LR
    const char *lr_text = " stacked LR = ";
    HAL_UART_Transmit(&huart2, (uint8_t*)lr_text, (uint16_t)strlen(lr_text), HAL_MAX_DELAY);
    print_uint32_hex(stacked_lr);
    HAL_UART_Transmit(&huart2, (uint8_t*)crlf, (uint16_t)strlen(crlf), HAL_MAX_DELAY);

    // Print CFSR
    const char *cfsr_text = "   CFSR    = ";
    HAL_UART_Transmit(&huart2, (uint8_t*)cfsr_text, (uint16_t)strlen(cfsr_text), HAL_MAX_DELAY);
    print_uint32_hex(cfsr);
    HAL_UART_Transmit(&huart2, (uint8_t*)crlf, (uint16_t)strlen(crlf), HAL_MAX_DELAY);

    // Print HFSR
    const char *hfsr_text = "   HFSR    = ";
    HAL_UART_Transmit(&huart2, (uint8_t*)hfsr_text, (uint16_t)strlen(hfsr_text), HAL_MAX_DELAY);
    print_uint32_hex(hfsr);
    HAL_UART_Transmit(&huart2, (uint8_t*)crlf, (uint16_t)strlen(crlf), HAL_MAX_DELAY);

    // Optionally, print the stack pointer value
    const char *sp_text = "   SP      = ";
    HAL_UART_Transmit(&huart2, (uint8_t*)sp_text, (uint16_t)strlen(sp_text), HAL_MAX_DELAY);
    print_uint32_hex(stacked_sp);
    HAL_UART_Transmit(&huart2, (uint8_t*)crlf, (uint16_t)strlen(crlf), HAL_MAX_DELAY);

    // Now loop forever (or reset)
    while (1)
    {
        __NOP();
    }
}

/* USER CODE END 0 */

/* External variables --------------------------------------------------------*/
extern UART_HandleTypeDef huart1;
extern TIM_HandleTypeDef htim6;

/* USER CODE BEGIN EV */

/* USER CODE END EV */

/******************************************************************************/
/*           Cortex-M4 Processor Interruption and Exception Handlers          */
/******************************************************************************/
/**
  * @brief This function handles Non maskable interrupt.
  */
void NMI_Handler(void)
{
  /* USER CODE BEGIN NonMaskableInt_IRQn 0 */

  /* USER CODE END NonMaskableInt_IRQn 0 */
  /* USER CODE BEGIN NonMaskableInt_IRQn 1 */
   while (1)
  {
  }
  /* USER CODE END NonMaskableInt_IRQn 1 */
}

/**
  * @brief This function handles Hard fault interrupt.
  */
void HardFault_Handler(void)
{
  /* USER CODE BEGIN HardFault_IRQn 0 */
    // On Cortex-M, when a HardFault occurs in thread mode, the CPU pushes registers
    // onto the stack (PSP).  We can figure out whether the CPU was using PSP or MSP
    // by examining bit-2 of LR (EXC_RETURN).  In FreeRTOS tasks run under PSP, so:
    __asm volatile
    (
        "TST lr, #4            \n"  // test bit-2 of LR.  If 0 → MSP, if 1 → PSP
        "ITE EQ                \n"  // if EQ = bit was zero (so MSP in use)
        "MRSEQ r0, MSP         \n"  //   r0 = MSP
        "MRSNE r0, PSP         \n"  // else r0 = PSP
        "B HardFault_Handler_C \n"  // branch to our C handler
    );

  
  /* USER CODE END HardFault_IRQn 0 */
  while (1)
  {
    /* USER CODE BEGIN W1_HardFault_IRQn 0 */
    /* USER CODE END W1_HardFault_IRQn 0 */
  }
}

/**
  * @brief This function handles Memory management fault.
  */
void MemManage_Handler(void)
{
  /* USER CODE BEGIN MemoryManagement_IRQn 0 */

  /* USER CODE END MemoryManagement_IRQn 0 */
  while (1)
  {
    /* USER CODE BEGIN W1_MemoryManagement_IRQn 0 */
    /* USER CODE END W1_MemoryManagement_IRQn 0 */
  }
}

/**
  * @brief This function handles Prefetch fault, memory access fault.
  */
void BusFault_Handler(void)
{
  /* USER CODE BEGIN BusFault_IRQn 0 */

  /* USER CODE END BusFault_IRQn 0 */
  while (1)
  {
    /* USER CODE BEGIN W1_BusFault_IRQn 0 */
    /* USER CODE END W1_BusFault_IRQn 0 */
  }
}

/**
  * @brief This function handles Undefined instruction or illegal state.
  */
void UsageFault_Handler(void)
{
  /* USER CODE BEGIN UsageFault_IRQn 0 */

  /* USER CODE END UsageFault_IRQn 0 */
  while (1)
  {
    /* USER CODE BEGIN W1_UsageFault_IRQn 0 */
    /* USER CODE END W1_UsageFault_IRQn 0 */
  }
}

/**
  * @brief This function handles Debug monitor.
  */
void DebugMon_Handler(void)
{
  /* USER CODE BEGIN DebugMonitor_IRQn 0 */

  /* USER CODE END DebugMonitor_IRQn 0 */
  /* USER CODE BEGIN DebugMonitor_IRQn 1 */

  /* USER CODE END DebugMonitor_IRQn 1 */
}

/******************************************************************************/
/* STM32L4xx Peripheral Interrupt Handlers                                    */
/* Add here the Interrupt Handlers for the used peripherals.                  */
/* For the available peripheral interrupt handler names,                      */
/* please refer to the startup file (startup_stm32l4xx.s).                    */
/******************************************************************************/

/**
  * @brief This function handles USART1 global interrupt.
  */
void USART1_IRQHandler(void)
{
  /* USER CODE BEGIN USART1_IRQn 0 */

  /* USER CODE END USART1_IRQn 0 */
  HAL_UART_IRQHandler(&huart1);
  /* USER CODE BEGIN USART1_IRQn 1 */

  /* USER CODE END USART1_IRQn 1 */
}

/**
  * @brief This function handles TIM6 global interrupt, DAC channel1 and channel2 underrun error interrupts.
  */
void TIM6_DAC_IRQHandler(void)
{
  /* USER CODE BEGIN TIM6_DAC_IRQn 0 */

  /* USER CODE END TIM6_DAC_IRQn 0 */
  HAL_TIM_IRQHandler(&htim6);
  /* USER CODE BEGIN TIM6_DAC_IRQn 1 */

  /* USER CODE END TIM6_DAC_IRQn 1 */
}

/* USER CODE BEGIN 1 */

/* USER CODE END 1 */
